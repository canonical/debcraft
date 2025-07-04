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

"""Main Debcraft Application."""

import craft_application

METADATA = craft_application.AppMetadata(
    name="debcraft",
    summary="Tool to create Debian Packages using a Craft workflow",
    ProjectClass=craft_application.models.Project,
)


class Application(craft_application.Application):
    """Debcraft application definition."""
