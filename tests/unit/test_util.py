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
        pytest.param("aarch64", "aarch64-linux-gnu", id="arch_aarch64"),
        pytest.param("armv7l", "arm-linux-gnueabihf", id="arch_armv7l"),
        pytest.param("ppc64le", "powerpc64le-linux-gnu", id="arch_pp64le"),
        pytest.param("riscv64", "riscv64-linux-gnu", id="arch_risc64v"),
        pytest.param("s390x", "s390x-linux-gnu", id="arch_s390x"),
        pytest.param("x86_64", "x86_64-linux-gnu", id="arch_x86_64"),
        pytest.param("i686", "i386-linux-gnu", id="arch_i686"),
        pytest.param(None, "aarch64-linux-gnu", id="arch_None"),
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


@pytest.mark.parametrize(
    ("versions", "max_ver"),
    [
        pytest.param(set(), None, id="empty"),
        pytest.param({"1.1"}, "1.1", id="single"),
        pytest.param({"1.2", "1.10", "1.9"}, "1.10", id="numeric"),
        pytest.param({"1.0~rc1", "1.0"}, "1.0", id="tilde"),
        pytest.param({"1.0-1~bp10+1", "1.0-1"}, "1.0-1", id="tilde-plus"),
        pytest.param({"1:0.5", "9.9"}, "1:0.5", id="epoch"),
        pytest.param({"1.0+b1", "1.0+b2", "1.0+a1"}, "1.0+b2", id="letter"),
        pytest.param({"2.4.1-1", "2.4.1-10", "2.4.1-2"}, "2.4.1-10", id="revision"),
    ],
)
def test_get_max_debian_version(versions, max_ver):
    assert util.get_max_debian_version(versions) == max_ver
