# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Debcraft-provided plugin registration."""

import craft_parts
from craft_parts.plugins.plugins import PluginType

from .rust_plugin import RustPlugin


def register() -> None:
    """Register Debcraft plugins for a given base."""
    craft_parts.plugins.register(get_plugins())


def get_plugins() -> dict[str, PluginType]:
    """Get a dict of Debcraft-specific plugins."""
    return {
        "rust": RustPlugin,
    }
