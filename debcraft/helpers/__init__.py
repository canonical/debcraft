# This file is part of debcraft.
#
# Copyright 2026 Canonical Ltd.
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

"""Debcraft helpers."""

from .gencontrol import Gencontrol
from .helpers import HelperGroup
from .makedeb import Makedeb
from .makeshlibs import Makeshlibs
from .md5sums import Md5sums
from .shlibdeps import Shlibdeps
from .strip import Strip


class BuildHelpers(HelperGroup):
    """Helpers used during build."""

    def _register(self) -> None:
        pass


class PackagingHelpers(HelperGroup):
    """Helpers used during package creation."""

    def _register(self) -> None:
        self._register_helper("strip", Strip)
        self._register_helper("md5sums", Md5sums)
        self._register_helper("makeshlibs", Makeshlibs)
        self._register_helper("shlibdeps", Shlibdeps)
        self._register_helper("gencontrol", Gencontrol)
        self._register_helper("makedeb", Makedeb)


__all__ = [
    "BuildHelpers",
    "HelperGroup",
    "PackagingHelpers",
]
