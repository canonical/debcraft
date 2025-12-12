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

import os
import pathlib
import subprocess
import tarfile
import tempfile
from typing import cast

import zstandard as zstd
from craft_application import services
from craft_platforms import BuildInfo
from typing_extensions import override

from debcraft import control, errors, models
from debcraft.services.lifecycle import Lifecycle
from debcraft.services.makeshlibs import MakeshlibsService
from debcraft.services.md5sums import Md5sumsService
from debcraft.services.strip import StripService

_ZSTD_COMPRESSION_LEVEL = 3


class Package(services.PackageService):
    """Package service subclass for Debcraft."""

    @override
    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
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
            lifecycle = cast(Lifecycle, self._services.lifecycle)
            prime = lifecycle.get_prime_dir(package_name)

            arch = _get_architecture(package, build_info)
            if not arch:
                continue

            deb = self._create_package(
                dest,
                project=project,
                package_name=package_name,
                arch=arch,
                prime_dir=prime,
            )
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
        self,
        dest: pathlib.Path,
        *,
        project: models.Project,
        package_name: str,
        arch: str,
        prime_dir: pathlib.Path,
    ) -> pathlib.Path:
        package = project.get_package(package_name)
        version = cast(str, package.version or project.version)
        deb_path = dest.absolute() / f"{package_name}_{version}_{arch}.deb"

        installed_size = _get_dir_size(prime_dir)

        deb_path.unlink(missing_ok=True)

        cast(StripService, self._services.get("strip")).run(prime_dir=prime_dir)

        with tempfile.TemporaryDirectory() as ctl_dir:
            control_dir = pathlib.Path(ctl_dir)

            _create_control_file(
                project=project,
                package_name=package_name,
                arch=arch,
                installed_size=installed_size,
                dest_dir=control_dir,
            )

            # Run helpers
            cast(Md5sumsService, self._services.get("md5sums")).run(
                prime_dir, dest_dir=control_dir
            )
            cast(MakeshlibsService, self._services.get("makeshlibs")).run(
                prime_dir, package_name, version, dest_dir=control_dir
            )

            _create_deb(deb_path, prime_dir=prime_dir, control_dir=control_dir)

            return deb_path


def _create_deb(
    deb_path: pathlib.Path, *, prime_dir: pathlib.Path, control_dir: pathlib.Path
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_tar = pathlib.Path(tmpdir, "data.tar.zst")
        control_tar = pathlib.Path(tmpdir, "control.tar.zst")
        debian_binary_file = pathlib.Path(tmpdir, "debian-binary")

        _create_tarball(root=prime_dir, dest_file=data_tar)
        _create_tarball(root=control_dir, dest_file=control_tar)
        debian_binary_file.write_text("2.0\n")

        cwd = pathlib.Path().absolute()
        try:
            os.chdir(tmpdir)

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


def _create_tarball(*, root: pathlib.Path, dest_file: pathlib.Path) -> None:
    """Create the data.tar.zst file containing the prime contents.

    :param root: Directory containing the files to package.
    :param dest_file: The tar file to be created.
    """
    with dest_file.open("wb") as data_zstd:
        zcomp = zstd.ZstdCompressor(level=_ZSTD_COMPRESSION_LEVEL)
        with zcomp.stream_writer(data_zstd) as comp:
            with tarfile.open(
                fileobj=comp, mode="w", format=tarfile.USTAR_FORMAT
            ) as tar:
                for entry in root.absolute().iterdir():
                    tar.add(entry, arcname=entry.name)


def _create_control_file(
    *,
    project: models.Project,
    package_name: str,
    arch: str,
    installed_size: int,
    dest_dir: pathlib.Path,
) -> None:
    """Create the control file containing package metadata.

    :param project: The project model.
    :param package_name: The name of the package being created.
    :param arch: The deb control architecture.
    :param installed_size: The size of installed files in bytes.
    :param dest_dir: Directory where the control file will be created.
    """
    package = project.get_package(package_name)

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

    output_file = dest_dir / "control"

    with output_file.open("w", encoding="utf-8", newline="\n") as f:
        encoder = control.Encoder(f)
        encoder.encode(ctl_data)


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
