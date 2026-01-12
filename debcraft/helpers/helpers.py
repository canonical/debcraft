#  This file is part of debcraft.
#
#  Copyright 2026 Canonical Ltd.
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

"""Debcraft helpers base."""

from abc import ABC, abstractmethod

from debcraft import errors


class Helper:
    """Debcraft helper base class."""


class HelperGroup(ABC):
    """A collection of Debcraft helpers."""

    def __init__(self) -> None:
        self._helper_class: dict[str, type[Helper]] = {}
        self._helper: dict[str, Helper | None] = {}
        self._register()

    @abstractmethod
    def _register(self) -> None:
        """Register all helpers in this helper group."""

    def _register_helper(self, name: str, helper_class: type[Helper]) -> None:
        self._helper_class[name] = helper_class
        self._helper[name] = None

    def get_helper(self, name: str) -> Helper:
        """Obtain the instance of the named helper.

        :param name: The name of the helper.
        :returns: The instance of the named helper.
        """
        if name not in self._helper_class:
            raise errors.DebcraftError(f"helper '{name}' is not registered.")

        helper = self._helper.get(name)
        if not helper:
            helper = self._helper_class[name]()
            self._helper[name] = helper

        return helper
