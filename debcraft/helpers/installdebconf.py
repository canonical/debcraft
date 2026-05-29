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

"""Debcraft installdebconf helper."""

import pathlib
from typing import Any

from craft_parts import ProjectInfo

from debcraft import models

from .helpers import Helper, install_package_control


class Installdebconf(Helper):
    """Debcraft installdebconf helper."""

    def run(
        self,
        *,
        project: models.Project,
        project_info: ProjectInfo,
        build_dir: pathlib.Path,
        partition_dir: pathlib.Path,
        install_dirs: dict[str, pathlib.Path],
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Install debconf files.

        :param project: the project model.
        :param build_dir: the directory containing the project being built.
        :param partition_dir: the work directory for partition data.
        :param install_dirs: mapping of partitions to install directories.
        """
        if not project.packages:
            return

        template_mapping = {
            "DEB_HOST_NAME": project_info.arch_build_for,
            "DEB_BUILD_NAME": project_info.arch_build_on,
            "DEB_TARGET_NAME": project_info.arch_build_for,
        }

        install_package_control(
            name="config",
            project=project,
            build_dir=build_dir,
            partition_dir=partition_dir,
            install_dirs=install_dirs,
            template_mapping=template_mapping,
        )

        install_package_control(
            name="templates",
            project=project,
            build_dir=build_dir,
            partition_dir=partition_dir,
            install_dirs=install_dirs,
            template_mapping=template_mapping,
        )
