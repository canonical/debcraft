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

"""Command-line interface entrypoint."""

from typing import Any

import craft_application
from craft_cli import Dispatcher

import debcraft
from debcraft import services


def _create_app() -> debcraft.Application:
    """Create a Debcraft application instance."""
    craft_application.ServiceFactory.register("package", services.Package)
    app_services = craft_application.ServiceFactory(
        app=debcraft.METADATA  # type: ignore[call-arg]
    )

    return debcraft.Application(app=debcraft.METADATA, services=app_services)


def get_app_info() -> tuple[Dispatcher, dict[str, Any]]:
    """Retrieve application info. Used by craft-cli's completion module."""
    app = _create_app()
    app._load_plugins()  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    dispatcher = app._create_dispatcher()  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    return dispatcher, app.app_config


def main() -> int:
    """Start up and run Debcraft."""
    app = _create_app()
    return app.run()
