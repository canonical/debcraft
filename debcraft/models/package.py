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
"""Model for defining deb binary packages."""

from typing import Literal

import pydantic
from craft_application import models
from craft_platforms import DebianArchitecture


class Package(models.CraftBaseModel):
    """A single binary package.

    The key in the dict where this is the value matches the package name ("Package")
    Each instance of this is roughly equivalent to a binary package stanza in the
    control file.
    See: https://www.debian.org/doc/debian-policy/ch-controlfields.html
    """

    architectures: Literal["any", "all"] | list[DebianArchitecture] = "any"
    summary: str | None = None  # defaults to the project summary
    description: str | None = None  # defaults to the project description

    version: str | None = None  # defaults to the project version

    # These need validating: https://github.com/canonical/debcraft/issues/42
    # https://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps
    depends: list[str] | None = None
    recommends: list[str] | None = None
    provides: list[str] | None = None
    breaks: list[str] | None = None
    replaces: list[str] | None = None
    conflicts: list[str] | None = None

    section: str | None = None

    passthrough: dict[str, str] = pydantic.Field(default_factory=dict)
    """Values that are passed directly into the control stanza for this package.

    Use of this key indicates something incomplete in debcraft.
    """
