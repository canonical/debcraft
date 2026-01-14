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

"""Tests for Debcraft helpers."""

import pytest
import pytest_mock
from debcraft import errors, util


@pytest.mark.parametrize(
    ("arch", "triplet"),
    [
        ("aarch64", "aarch64-linux-gnu"),
        ("armv7l", "arm-linux-gnueabihf"),
        ("ppc64le", "powerpc64le-linux-gnu"),
        ("riscv64", "riscv64-linux-gnu"),
        ("s390x", "s390x-linux-gnu"),
        ("x86_64", "x86_64-linux-gnu"),
        ("i686", "i386-linux-gnu"),
        (None, "aarch64-linux-gnu"),
    ],
)
def test_get_arch_triplet(
    mocker: pytest_mock.MockerFixture, arch: str | None, triplet: str
):
    mocker.patch("platform.machine", return_value="aarch64")
    arch_triplet = util.get_arch_triplet(arch)
    assert arch_triplet == triplet


def test_get_arch_triplet_error():
    expected = "arch triplet is not defined for arch 'other'"
    with pytest.raises(errors.DebcraftError, match=expected):
        util.get_arch_triplet("other")
