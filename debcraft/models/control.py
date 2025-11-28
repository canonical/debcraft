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

"""Debian control file model for Debcraft."""

from craft_application import models
from pydantic import ConfigDict


def _field_alias(field_name: str) -> str:
    parts = field_name.replace("_", "-").split("-")
    capitalized_parts = [p.capitalize() for p in parts]
    return "-".join(capitalized_parts)


class DebianControl(models.CraftBaseModel):
    """Debian control file definition."""

    model_config = ConfigDict(alias_generator=_field_alias, populate_by_name=True)

    package: str
    source: str
    version: str
    architecture: str | list[str]
    maintainer: str
    installed_size: int
    depends: list[str] | None = None
    recommends: list[str] | None = None
    conflicts: list[str] | None = None
    breaks: list[str] | None = None
    replaces: list[str] | None = None
    provides: list[str] | None = None
    section: str
    priority: str
    description: str
    original_maintainer: str | None = None
    uploaders: list[str] | None = None
