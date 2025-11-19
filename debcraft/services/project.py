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

"""Project service for debcraft."""

import craft_platforms
from craft_application import services


class Project(services.ProjectService):
    """The service for rendering Debcraft projects."""

    def _app_render_legacy_platforms(self) -> dict[str, craft_platforms.PlatformDict]:
        """Provide the default platforms if no platforms are declared.

        This sets the platforms to be the broadest possible set of platforms without
        cross compiling. That is, it builds platform-independent packages on any
        architecture and then enables all architectures without cross-compilation.
        """
        return {
            "all": {
                "build-on": sorted(craft_platforms.DebianArchitecture),
                "build-for": ["all"],
            },
            **{
                architecture.value: {
                    "build-on": [architecture.value],
                    "build-for": [architecture.value],
                }
                for architecture in craft_platforms.DebianArchitecture
            },
        }
