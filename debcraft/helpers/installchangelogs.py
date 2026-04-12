#  This file is part of debcraft.
#
#  Copyright 2026 Canonical Ltd.
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

"""Debcraft installchangelogs helper."""

import gzip
import pathlib
import shutil
import tempfile
from typing import Any

from craft_cli import emit

from debcraft import models

from .helpers import Helper


class Installchangelogs(Helper):
    """Debcraft installchangelogs helper."""

    def run(
        self,
        *,
        project: models.Project,
        build_dir: pathlib.Path,
        install_dirs: dict[str, pathlib.Path],
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Install changelog files.

        :param build_dir: the directory containing the project being built.
        :param install_dirs: mapping of partitions to install directories.
        """
        if not project.packages:
            return

        # Pending: add support to handle native/non-native packages
        is_native = False

        changelog_name = "changelog" if is_native else "changelog.Debian"

        # Install changelog and NEWS files for all packages
        # Support for <package_name>.NEWS is not implemented. Use organize
        # to install them into the appropriate packages.
        for debian_dir in ("debcraft", "debian"):
            changelog = build_dir / debian_dir / "changelog"
            if changelog.is_file():
                _install_doc(
                    changelog,
                    install_dirs,
                    changelog_name,
                )
                break

        for debian_dir in ("debcraft", "debian"):
            news = build_dir / debian_dir / "NEWS"
            if news.is_file():
                _install_doc(
                    news,
                    install_dirs,
                    "NEWS.Debian",
                )
                break


def _install_doc(
    file: pathlib.Path, install_dirs: dict[str, pathlib.Path], name: str
) -> None:
    """Install and compress files to usr/share/doc/package."""
    name_gz = name + ".gz"
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_file = pathlib.Path(tmp_dir, name_gz)

        with file.open("rb") as f_in:
            with temp_file.open("wb") as f_out:
                with gzip.GzipFile(
                    fileobj=f_out, mode="wb", compresslevel=9, mtime=0, filename=""
                ) as gz:
                    shutil.copyfileobj(f_in, gz)

        for partition, install_dir in install_dirs.items():
            if partition in ("default", "build"):
                continue

            package = partition.removeprefix("package/")
            changelog_file = f"usr/share/doc/{package}/{name_gz}"
            dest = install_dir / changelog_file
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_file, dest)
            dest.chmod(0o644)
            emit.progress(f"Install changelog: {changelog_file}")
