#  This file is part of debcraft.
#
#  Copyright 2023-2025 Canonical Ltd.
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
"""Tests for debcraft's gencontrol helper."""

import pytest
from debcraft.helpers import gencontrol


@pytest.mark.parametrize(
    ("deps", "user_deps", "result"),
    [
        ([], [], []),
        (["a"], [], ["a"]),
        ([], ["b"], ["b"]),
        (["a"], ["b"], ["a", "b"]),
        (["a ver1"], [], ["a ver1"]),
        ([""], ["a ver2"], ["a ver2"]),
        (["a ver1"], ["a ver2"], ["a ver2"]),
        (["a ver1", "b ver3"], ["a ver2", "c ver4"], ["a ver2", "b ver3", "c ver4"]),
    ],
)
def test_filter_dependencies(deps: list[str], user_deps: list[str], result: list[str]):
    res = gencontrol._filter_dependencies(deps, user_deps)
    assert res == result
