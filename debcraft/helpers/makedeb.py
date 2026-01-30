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

"""Debcraft makedeb helper service."""

import os
import pathlib
import subprocess
import tarfile
from typing import Any, cast

import zstandard as zstd
from craft_cli import emit

from debcraft import models

from .helpers import Helper

_ZSTD_COMPRESSION_LEVEL = 3


class Makedeb(Helper):
    """Debcraft makedeb helper."""

    def run(
        self,
        *,
        project: models.Project,
        package_name: str,
        arch: str,
        prime_dir: pathlib.Path,
        control_dir: pathlib.Path,
        deb_dir: pathlib.Path,
        output_dir: pathlib.Path,
        deb_list: list[pathlib.Path],
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Create deb package."""
        package = project.get_package(package_name)
        version = cast(str, package.version or project.version)
        deb_name = f"{package_name}_{version}_{arch}.deb"
        output_file = output_dir.absolute() / deb_name

        output_file.unlink(missing_ok=True)

        data_tar = deb_dir / "data.tar.zst"
        control_tar = deb_dir / "control.tar.zst"
        debian_binary_file = deb_dir / "debian-binary"

        _create_tarball(root=prime_dir, dest_file=data_tar)
        _create_tarball(root=control_dir, dest_file=control_tar)
        debian_binary_file.write_text("2.0\n")

        cwd = pathlib.Path().absolute()
        try:
            os.chdir(deb_dir)
            emit.progress(f"Create deb package {deb_name}")

            # Order of files added to the deb file is important. The
            # debian-binary file must come first, followed by the control
            # tarball and then the data tarball.
            subprocess.run(
                [
                    "ar",
                    "rc",
                    output_file,
                    "debian-binary",
                    "control.tar.zst",
                    "data.tar.zst",
                ],
                check=True,
            )
        finally:
            os.chdir(cwd)

        deb_list.append(output_file)


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
