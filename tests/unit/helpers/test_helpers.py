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

"""Tests for debcraft's helpers subsystem."""

import pytest
from debcraft import errors
from debcraft.helpers import helpers


class MyHelper(helpers.Helper):
    def run(self) -> None:
        pass


class MyGroup(helpers.HelperGroup):
    def _register(self):
        self._register_helper("test", MyHelper)


def test_get_helper():
    group = MyGroup()
    test_helper = group.get_helper("test")
    assert isinstance(test_helper, MyHelper)


def test_get_helper_error():
    group = MyGroup()
    with pytest.raises(errors.DebcraftError, match="helper .* is not registered"):
        group.get_helper("does-not-exist")
