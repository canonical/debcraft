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
"""Unit tests for the debcraft project model."""

import pytest
from craft_providers import bases
from debcraft.models import project


@pytest.mark.parametrize(
    "name",
    [
        "3cpio",
        "7zip",
        "apt",
        "ed",
        "libqt6waylandcompositorpresentationtime6t64",
        "linux-headers-6.17.0-6",
        "allowed-to-end-with+",
        "allowed-to-end-with-",
        "allowed-to-end-with.",
    ],
)
def test_validate_debian_package_name_success(name: str):
    project._validate_debian_package_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "a",
        "libqt6waylandcompositorpresentationtime6t64:amd64",
        "jeb!",
        "Jebediah Kerman",
        "+start-not-allowed",
        "-start-not-allowed",
        ".start-not-allowed",
    ],
)
def test_validate_debian_package_name_error(name: str):
    with pytest.raises(ValueError, match="^package names must"):
        project._validate_debian_package_name(name)


@pytest.mark.parametrize(
    "extra_project_params",
    [
        {"adopt-info": "my-part", "parts": {"my-part": {"plugin": "nil"}}},
    ],
)
def test_adopt_info_valid_part_name_success(default_project_raw):
    assert "adopt-info" in default_project_raw
    project.Project.model_validate(default_project_raw)


@pytest.mark.parametrize(
    "extra_project_params",
    [
        {"adopt-info": "my-part"},
    ],
)
def test_adopt_info_valid_part_name_error(default_project_raw):
    assert "adopt-info" in default_project_raw
    with pytest.raises(
        ValueError, match="'adopt-info' field must refer to the name of a part."
    ):
        project.Project.model_validate(default_project_raw)


@pytest.mark.parametrize(
    ("project_name", "extra_packages", "partitions"),
    [
        pytest.param(
            "myproject", {}, ["default", "package/package-1"], id="no extra package"
        ),
        pytest.param(
            "myproject",
            {"myproject": {"version": "1"}},
            ["package/myproject", "package/package-1"],
            id="package with same name",
        ),
        pytest.param(
            "myproject",
            {"other": {"version": "1"}},
            ["default", "package/package-1", "package/other"],
            id="package with different name",
        ),
    ],
)
def test_default_partition(
    default_project_raw, project_name, extra_packages, partitions
):
    default_project_raw["name"] = project_name
    for name, value in extra_packages.items():
        default_project_raw["packages"][name] = value
    pprj = project.PackagesProject.unmarshal(default_project_raw)
    assert pprj.get_partitions() == partitions


@pytest.mark.parametrize(
    "base", ["ubuntu@22.04", "ubuntu@24.04", "ubuntu@26.04", "ubuntu@26.10"]
)
def test_project_base_valid(default_project_raw, base: str):
    default_project_raw["base"] = base
    project.Project.model_validate(default_project_raw)


def test_project_base_invalid(default_project_raw):
    default_project_raw["base"] = "ubuntu@20.04"
    with pytest.raises(ValueError, match="base"):
        project.Project.model_validate(default_project_raw)


@pytest.mark.parametrize("build_base", [None, "ubuntu@24.04", "ubuntu@26.04", "devel"])
def test_project_build_base_valid(default_project_raw, build_base):
    default_project_raw["build-base"] = build_base
    project.Project.model_validate(default_project_raw)


def test_project_build_base_invalid(default_project_raw):
    default_project_raw["build-base"] = "ubuntu@26.10"
    with pytest.raises(ValueError, match="build-base"):
        project.Project.model_validate(default_project_raw)


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        ("devel", bases.get_base_alias(("ubuntu", "devel"))),
        ("ubuntu@24.04", bases.get_base_alias(("ubuntu", "24.04"))),
    ],
)
def test_providers_base_success(base: str, expected):
    assert project.Project._providers_base(base) == expected


def test_providers_base_error():
    with pytest.raises(ValueError, match="Unknown base"):
        project.Project._providers_base("not-a-base")


def test_get_devel_bases():
    devel_bases = list(project.Project._get_devel_bases())

    assert len(devel_bases) == 1
    assert devel_bases[0].current_devel_base is project.BuilddBaseAlias.STONKING
    assert devel_bases[0].devel_base is project.BuilddBaseAlias.DEVEL
