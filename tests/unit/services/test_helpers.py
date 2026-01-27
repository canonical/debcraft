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
from debcraft.helpers import md5sums, strip
from debcraft.services import helper


def test_install_helpers_runner(
    mocker, tmp_path, default_project, project_service, build_plan_service
):
    mock_run = mocker.patch.object(strip.Strip, "run")
    lifecycle = mocker.MagicMock()
    lifecycle.get_prime_dir.return_value = tmp_path

    step_info = mocker.MagicMock()
    step_info.part_build_dir = "build-dir"
    step_info.part_install_dir = "install-dir"
    step_info.part_name = "my-part"

    my_runner = helper.InstallHelpersRunner(
        project=default_project,
        build_info=build_plan_service.plan()[0],
        step_info=step_info,
        lifecycle=lifecycle,
    )
    with my_runner as runner:
        runner.run("strip", arg="foo")
        with pytest.raises(ValueError, match="is not registered"):
            runner.run("other")

    assert mock_run.mock_calls == [
        call(
            step_info=step_info,
            build_dir="build-dir",
            install_dir="install-dir",
            project=default_project,
            part_name="my-part",
            arg="foo",
        )
    ]


def test_packaging_helpers_runner(
    mocker, tmp_path, default_project, project_service, build_plan_service
):
    mock_run = mocker.patch.object(md5sums.Md5sums, "run")
    mocker.patch("debcraft.services.helper._get_architecture", return_value="arm64")
    lifecycle = mocker.MagicMock()
    lifecycle.get_prime_dir.return_value = tmp_path

    my_runner = helper.PackagingHelpersRunner(
        project=default_project,
        build_info=build_plan_service.plan()[0],
        lifecycle=lifecycle,
    )
    with my_runner as runner:
        runner.run("md5sums", arg="foo")
        runner_tmp_path = pathlib.Path(runner._temp_dir.name)
        with pytest.raises(ValueError, match="is not registered"):
            runner.run("other")

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
