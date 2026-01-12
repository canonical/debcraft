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
"""Tests for debcraft's package service."""

import craft_platforms
import pytest
from debcraft import models
from debcraft.services import helper


@pytest.mark.parametrize(
    ("source_archs", "binary_arch"),
    [
        ("any", "arm64"),
        ("all", "all"),
        (["arm64"], "arm64"),
        (["amd64", "arm64"], "arm64"),
        (["amd64", "s390x"], None),
        ([], None),
    ],
)
def test_get_architecture(source_archs, binary_arch):
    info = craft_platforms.BuildInfo(
        "foo",
        craft_platforms.DebianArchitecture.ARM64,
        craft_platforms.DebianArchitecture.ARM64,
        craft_platforms.DistroBase.from_str("ubuntu@22.04"),
    )
    pkg = models.Package(architectures=source_archs)
    arch = helper._get_architecture(pkg, info)
    assert arch == binary_arch
