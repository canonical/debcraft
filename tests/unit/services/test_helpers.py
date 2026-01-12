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
"""Tests for debcraft's helper service."""

import pathlib
from unittest.mock import call

import craft_platforms
import pytest
from debcraft import models
from debcraft.helpers import helpers
from debcraft.services import helper


class MyHelper(helpers.Helper):
    def run(self, **kwargs):
        pass


class MyGroup(helpers.HelperGroup):
    def _register(self):
        self._register_helper("test", MyHelper)


def test_helper_runner(
    mocker, tmp_path, default_project, project_service, build_plan_service
):
    mock_run = mocker.patch.object(MyHelper, "run")
    mocker.patch("debcraft.services.helper._get_architecture", return_value="arm64")
    lifecycle = mocker.MagicMock()
    lifecycle.get_prime_dir.return_value = tmp_path

    my_group = MyGroup()
    my_runner = helper.HelperRunner(
        project=default_project,
        build_info=build_plan_service.plan()[0],
        lifecycle=lifecycle,
        helpers=my_group,
    )
    with my_runner as runner:
        runner.run("test", arg="foo")

    runner_tmp_path = pathlib.Path(runner._temp_dir.name)

    assert mock_run.mock_calls == [
        call(
            prime_dir=tmp_path,
            arch="arm64",
            control_dir=runner_tmp_path / "package-1" / "control",
            state_dir=runner_tmp_path / "package-1" / "state",
            deb_dir=runner_tmp_path / "package-1" / "deb",
            project=default_project,
            package_name="package-1",
            state_dir_map={"package-1": runner_tmp_path / "package-1" / "state"},
            arg="foo",
        )
    ]


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
