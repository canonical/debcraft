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
"""Tests for debcraft's gencontrol helper."""

import textwrap

import pytest
from debcraft.helpers import gencontrol


def test_run(tmp_path, default_project):
    prime_dir = tmp_path / "prime"
    control_dir = tmp_path / "control"
    state_dir = tmp_path / "state"

    prime_dir.mkdir()
    control_dir.mkdir()
    state_dir.mkdir()

    shlibdeps_file = state_dir / "shlibdeps"
    shlibdeps_file.write_text("libfoo 5 libfoo5 (>= 5.1.2)\n")

    helper = gencontrol.Gencontrol()
    helper.run(
        project=default_project,
        package_name="package-1",
        arch="arm64",
        prime_dir=prime_dir,
        control_dir=control_dir,
        state_dir=state_dir,
    )

    content = (control_dir / "control").read_text()
    assert content == textwrap.dedent(
        """\
        Package: package-1
        Source: fake-project
        Version: 2.0
        Architecture: arm64
        Maintainer: Mike Maintainer <someone@example.com>
        Installed-Size: 0
        Depends: libfoo 5 libfoo5 (>= 5.1.2)
        Section: libs
        Priority: optional
        Description: A package
         Really a package
        """
    )


@pytest.mark.parametrize(
    ("deps", "user_deps", "result"),
    [
        pytest.param([], [], [], id="empty"),
        pytest.param(["a"], [], ["a"], id="only-deps"),
        pytest.param([], ["b"], ["b"], id="only-user-deps"),
        pytest.param(["a"], ["b"], ["a", "b"], id="merge-deps"),
        pytest.param(["a ver 1"], [], ["a ver 1"], id="keep-deps-version"),
        pytest.param([""], ["a ver 2"], ["a ver 2"], id="keep-user-deps-version"),
        pytest.param(
            ["a ver 1"], ["a ver 2"], ["a ver 2"], id="merge-deps-with-version"
        ),
        pytest.param(
            ["a ver 1", "b ver 3"],
            ["a ver 2", "c ver 4"],
            ["a ver 2", "b ver 3", "c ver 4"],
            id="override-deps",
        ),
    ],
)
def test_filter_dependencies(deps: list[str], user_deps: list[str], result: list[str]):
    res = gencontrol._filter_dependencies(deps, user_deps)
    assert res == result
