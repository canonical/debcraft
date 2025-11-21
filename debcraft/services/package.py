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

import pathlib
import tarfile
from typing import cast

from craft_application import services

from debcraft import models


class Package(services.PackageService):
    """Package service subclass for Debcraft."""

    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        self.write_metadata(prime_dir)
        project = self._services.get("project").get()
        build_plan = self._services.get("build_plan").plan()[0]

        binary_package_name = (
            f"{project.name}_{project.version}_{build_plan.platform}.tar.xz"
        )
        with tarfile.open(dest / binary_package_name, mode="w:xz") as tar:
            tar.add(prime_dir, arcname=".", recursive=True)
        return [dest / binary_package_name]

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
