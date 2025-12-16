# This file is part of debcraft.
#
# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Debcraft services."""

from craft_application.services import ServiceFactory
from craft_application.services.buildplan import BuildPlanService as BuildPlan


def register_services() -> None:
    """Register debcraft services to the service factory."""
    _register("package", "Package", module="debcraft.services.package")
    _register("project", "Project", module="debcraft.services.project")
    _register("lifecycle", "Lifecycle", module="debcraft.services.lifecycle")
    _register("strip", "StripService", module="debcraft.services.strip")
    _register("md5sums", "Md5sumsService", module="debcraft.services.md5sums")
    _register("makeshlibs", "MakeshlibsService", module="debcraft.services.makeshlibs")
    _register("gencontrol", "GencontrolService", module="debcraft.services.gencontrol")
    _register("makedeb", "MakedebService", module="debcraft.services.makedeb")


def _register(name: str, classname: str, *, module: str) -> None:
    ServiceFactory.register(name, classname, module=module)


__all__ = ["BuildPlan", "ServiceFactory"]
