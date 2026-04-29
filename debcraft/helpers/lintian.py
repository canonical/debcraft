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

"""Debcraft lintian helper."""

import pathlib
from typing import Any

from debcraft import models

from .helpers import Helper, install_package_data


class Lintian(Helper):
    """Debcraft lintian helper."""

    def run(
        self,
        *,
        project: models.Project,
        build_dir: pathlib.Path,
        install_dirs: dict[str, pathlib.Path],
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Install lintian-overrides files.

        :param build_dir: the directory containing the project being built.
        :param install_dirs: mapping of partitions to install directories.
        """
        if not project.packages:
            return

        # Map package names to lintian files in the debian directory.
        install_package_data(
            name="lintian-overrides",
            dest_dir=pathlib.Path("usr/share/lintian/overrides"),
            project=project,
            build_dir=build_dir,
            install_dirs=install_dirs,
        )
