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

"""Debcraft gencontrol helper service."""

import pathlib
from typing import Any

from craft_cli import emit

from debcraft import control, errors, models

from .helper import HelperService


class GencontrolService(HelperService):
    """Debcraft gencontrol helper service."""

    def run(
        self,
        *,
        project: models.Project,
        package_name: str,
        arch: str,
        prime_dir: pathlib.Path,
        control_dir: pathlib.Path,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Create the control file containing package metadata.

        :param project: The project model.
        :param package_name: The name of the package being created.
        :param arch: The deb control architecture.
        :param prime_dir: Directory containing the package payload files.
        :param control_dir: Directory where the control file will be created.
        """
        package = project.get_package(package_name)
        installed_size = _get_dir_size(prime_dir)

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
            raise errors.DebcraftError(
                f"package {package_name} description was not set"
            )

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

        emit.progress(f"Create control file for package {package_name}")
        output_file = control_dir / "control"

        with output_file.open("w", encoding="utf-8", newline="\n") as f:
            encoder = control.Encoder(f)
            encoder.encode(ctl_data)


def _get_dir_size(path: pathlib.Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
