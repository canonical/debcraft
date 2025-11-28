#  This file is part of debcraft.
#
#  Copyright 2025 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Package service for debcraft."""

from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import tarfile
import tempfile
from typing import cast

import zstandard as zstd
from craft_application import services
from craft_platforms import BuildInfo

from debcraft import control, errors, models
from debcraft.services.lifecycle import Lifecycle

_ZSTD_COMPRESSION_LEVEL = 3


class Package(services.PackageService):
    """Package service subclass for Debcraft."""

    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:  # noqa: ARG002
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        project = cast(models.Project, self._services.get("project").get())
        build_info = self._services.get("build_plan").plan()[0]

        if not project.packages:
            return []

        debs: list[pathlib.Path] = []
        for package_name, package in project.packages.items():
            prime = cast(Lifecycle, self._services.lifecycle).get_prime_dir(
                package_name
            )

            arch = _get_architecture(package, build_info)
            if not arch:
                continue

            deb = _create_package(dest, project, package_name, arch, prime)
            debs.append(deb)

        return debs

    @property
    def metadata(self) -> models.Metadata:
        """Generate the metadata.yaml model for the output file."""
        project = cast(models.Project, self._services.get("project").get())
        build_plan = self._services.get("build_plan").plan()[0]

        return models.Metadata(
            name=project.name,
            version=cast(str, project.version),
            architecture=build_plan.build_for,
        )


def _create_package(
    dest: pathlib.Path,
    project: models.Project,
    package_name: str,
    arch: str,
    prime_dir: pathlib.Path,
) -> pathlib.Path:
    package = project.get_package(package_name)
    version = package.version or project.version
    cwd = pathlib.Path().absolute()
    deb_path = dest.absolute() / f"{package_name}_{version}_{arch}.deb"

    installed_size = _get_dir_size(prime_dir)

    deb_path.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            _create_data_file(pathlib.Path(tmpdir), prime_dir)
            _create_control_file(
                pathlib.Path(tmpdir),
                project,
                package_name,
                arch,
                installed_size,
                prime_dir,
            )
            pathlib.Path("debian-binary").write_text("2.0\n")

            # Order of files added to the deb file is important. The
            # debian-binary file must come first, followed by the control
            # tarball and then the data tarball.
            subprocess.run(
                [
                    "ar",
                    "rc",
                    deb_path,
                    "debian-binary",
                    "control.tar.zst",
                    "data.tar.zst",
                ],
                check=True,
            )
        finally:
            os.chdir(cwd)

    return deb_path


def _create_data_file(path: pathlib.Path, prime_dir: pathlib.Path) -> None:
    """Create the data.tar.zst file containing the prime contents.

    :param path: Directory where the data.tar.zst file will be created.
    :param prime_dir: Directory containing the files to package.
    """
    data_path = path / "data.tar.zst"
    with data_path.open("wb") as data_zstd:
        zcomp = zstd.ZstdCompressor(level=_ZSTD_COMPRESSION_LEVEL)
        with zcomp.stream_writer(data_zstd) as comp:
            with tarfile.open(
                fileobj=comp, mode="w", format=tarfile.USTAR_FORMAT
            ) as tar:
                for entry in prime_dir.absolute().iterdir():
                    tar.add(entry, arcname=entry.name)


def _create_control_file(
    path: pathlib.Path,
    project: models.Project,
    package_name: str,
    arch: str,
    installed_size: int,
    prime_dir: pathlib.Path,
) -> None:
    """Create the control.tar.zst file containing package metadata.

    :param path: Directory where the control.tar.zst file will be created.
    :param project: The project model.
    :param arch: The deb control architecture.
    """
    package = project.get_package(package_name)
    control_path = path / "control.tar.zst"

    # To be moved to model validation after we stabilize contents.
    version = package.version or project.version
    if not version:
        raise errors.DebcraftError(f"package {package_name} version was not set")

    section = package.section or project.section
    if not section:
        raise errors.DebcraftError(f"package {package_name} section was not set")

    summary = package.summary or project.summary
    if not summary:
        raise errors.DebcraftError(f"package {package_name} summary was not set")

    description = package.description or project.description
    if not description:
        raise errors.DebcraftError(f"package {package_name} description was not set")

    # Change to use package data from the project model
    ctl_data = models.DebianBinaryPackageControl(
        package=package_name,
        source=project.name,
        version=version,
        architecture=arch,
        maintainer=project.maintainer,
        section=section,
        installed_size=int(installed_size / 1024),
        depends=package.depends,
        priority=project.priority.value or "optional",
        description=summary + "\n" + description,
        original_maintainer=project.original_maintainer,
        uploaders=project.uploaders,
    )

    ctlfile = pathlib.Path("control")
    md5file = pathlib.Path("md5sums")

    with ctlfile.open("w", encoding="utf-8", newline="\n") as f:
        encoder = control.Encoder(f)
        encoder.encode(ctl_data)

    _create_md5sums(prime_dir, md5file)

    with control_path.open("wb") as control_zstd:
        zcomp = zstd.ZstdCompressor(level=_ZSTD_COMPRESSION_LEVEL)
        with zcomp.stream_writer(control_zstd) as comp:
            with tarfile.open(
                fileobj=comp, mode="w", format=tarfile.USTAR_FORMAT
            ) as tar:
                tar.add("control")
                tar.add("md5sums")

    ctlfile.unlink()
    md5file.unlink()


def _get_dir_size(path: pathlib.Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _get_architecture(package: models.Package, build_info: BuildInfo) -> str | None:
    if package.architectures == "any":
        return build_info.build_for

    if package.architectures == "all":
        return "all"

    if build_info.build_for in package.architectures:
        return build_info.build_for

    return None


def _md5sum(path: pathlib.Path) -> str:
    """Compute MD5 checksum of a file."""
    h = hashlib.md5()  # noqa: S324
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _create_md5sums(root: pathlib.Path, output_file: pathlib.Path) -> None:
    """Walk subtree and write md5 checksums with relative paths."""
    with output_file.open("w") as out:
        for file in root.rglob("*"):
            if file.is_file():
                checksum = _md5sum(file)
                relpath = file.relative_to(root)
                out.write(f"{checksum}  {relpath}\n")
