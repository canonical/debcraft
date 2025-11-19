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
import textwrap
from typing import cast

import craft_application
import zstandard as zstd
from craft_application import services
from craft_platforms import BuildInfo

from debcraft import models

_ZSTD_COMPRESSION_LEVEL = 3


class Package(services.PackageService):
    """Package service subclass for Debcraft."""

    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        project = self._services.get("project").get()
        build_plan = self._services.get("build_plan").plan()[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = pathlib.Path().absolute()
            deb_name = (
                dest.absolute()
                / f"{project.name}_{project.version}_{build_plan.platform}.deb"
            )

            try:
                os.chdir(tmpdir)
                _create_data_file(pathlib.Path(tmpdir), prime_dir)
                _create_control_file(pathlib.Path(tmpdir), project, build_plan)

                pathlib.Path("debian-binary").write_text("2.0\n")
                subprocess.run(
                    [
                        "ar",
                        "rcs",
                        deb_name,
                        "debian-binary",
                        "control.tar.zstd",
                        "data.tar.zstd",
                    ],
                    check=True,
                )
            finally:
                os.chdir(cwd)

        return [deb_name]

    @property
    def metadata(self) -> models.Metadata:
        """Generate the metadata.yaml model for the output file."""
        project = cast(models.Project, self._services.get("project").get())
        build_plan = self._services.get("build_plan").plan()[0]

        return models.Metadata(
            name=project.name,
            version=cast(str, project.version),
            base=project.base,
            architecture=build_plan.build_for,
        )


def _create_data_file(path: pathlib.Path, prime_dir: pathlib.Path) -> None:
    """Create the data.tar.zstd file containing the prime contents.

    :param path: Directory where the data.tar.zstd file will be created.
    :param prime_dir: Directory containing the files to package.
    """
    # This should return md5sums to use in the control metadata
    data_path = path / "data.tar.zstd"
    with data_path.open("wb") as data_zstd:
        zcomp = zstd.ZstdCompressor(level=_ZSTD_COMPRESSION_LEVEL)
        with zcomp.stream_writer(data_zstd) as comp:
            with tarfile.open(fileobj=comp, mode="w") as tar:
                tar.add(prime_dir.absolute(), arcname=".")


def _create_control_file(
    path: pathlib.Path, project: craft_application.models.Project, build_plan: BuildInfo
) -> None:
    """Create the control.tar.zstd file containing package metadata.

    :param path: Directory where the control.tar.zstd file will be created.
    :param project: The project model.
    :param build_plan: Platform information.
    """
    control_path = path / "control.tar.zstd"

    # Change to use package data from the project model
    control_data = textwrap.dedent(
        f"""\
        Package: {project.name}
        Version: {project.version}
        Architecture: {build_plan.platform}
    """
    )
    control = pathlib.Path("control")
    control.write_text(control_data)

    with control_path.open("wb") as control_zstd:
        zcomp = zstd.ZstdCompressor(level=_ZSTD_COMPRESSION_LEVEL)
        with zcomp.stream_writer(control_zstd) as comp:
            with tarfile.open(fileobj=comp, mode="w") as tar:
                tar.add("control")

    control.unlink()
