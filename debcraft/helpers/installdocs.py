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

"""Debcraft installdocs helper."""

import pathlib
import shutil
from typing import Any

from craft_cli import emit

from debcraft import models

from .helpers import Helper


class Installdocs(Helper):
    """Debcraft installdocs helper."""

    def run(
        self,
        *,
        project: models.Project,
        build_dir: pathlib.Path,
        install_dirs: dict[str, pathlib.Path],
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Install copyright file.

        :param build_dir: the directory containing the project being built.
        :param install_dirs: mapping of partitions to install directories.
        """
        if not project.packages:
            return

        # Install copyright file in all packages
        for debian_dir in ("debcraft", "debian"):
            cfile = build_dir / debian_dir / "copyright"
            if not cfile.is_file():
                continue

            for partition, install_dir in install_dirs.items():
                if partition in ("default", "build"):
                    continue

                package = partition.removeprefix("package/")
                copyright_file = f"usr/share/doc/{package}/copyright"
                dest = install_dir / copyright_file
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(cfile, dest)
                dest.chmod(0o644)
                emit.progress(f"Install copyright: {copyright_file}")

            break
