#  This file is part of debcraft.
#
#  Copyright 2025-2026 Canonical Ltd.
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

import pathlib
from typing import cast

from craft_application import services
from typing_extensions import override

from debcraft import models
from debcraft.services.helper import HelperService


class Package(services.PackageService):
    """Package service subclass for Debcraft."""

    @override
    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        project = cast(models.Project, self._services.get("project").get())
        if not project.packages:
            return []

        helper_service = cast(HelperService, self._services.helper)
        debs: list[pathlib.Path] = []

        with helper_service.packaging_helpers() as helper:
            helper.run("strip")
            helper.run("md5sums")
            helper.run("makeshlibs")
            helper.run("shlibdeps")
            helper.run("gencontrol")
            helper.run("makedeb", output_dir=dest, deb_list=debs)

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
