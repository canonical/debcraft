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

from debcraft import errors
from debcraft.models import project
from debcraft.models.package import Package


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


# Tests for Project.get_package()
def test_get_package_success(default_project):
    """Test that get_package returns the correct package."""
    package = default_project.get_package("package-1")
    assert package.version == "2.0"


@pytest.mark.parametrize(
    "extra_project_params",
    [
        {"packages": None},
    ],
)
def test_get_package_no_packages_defined(default_project):
    """Test that get_package raises an error when no packages are defined."""
    with pytest.raises(errors.DebcraftError, match="no packages defined"):
        default_project.get_package("any-package")


def test_get_package_not_found(default_project):
    """Test that get_package raises an error when package is not found."""
    with pytest.raises(
        errors.DebcraftError, match="package nonexistent-package is not defined"
    ):
        default_project.get_package("nonexistent-package")


# Tests for PackagesProject.get_partitions()
def test_get_partitions_no_packages():
    """Test that get_partitions returns ['default'] when no packages are defined."""
    packages_project = project.PackagesProject(packages=None)
    result = packages_project.get_partitions()
    assert result == ["default"]


def test_get_partitions_with_packages():
    """Test that get_partitions returns correct list when packages are defined."""
    packages_project = project.PackagesProject(
        packages={
            "pkg-a": Package(version="1.0"),
            "pkg-b": Package(version="2.0"),
        }
    )
    result = packages_project.get_partitions()
    assert result == ["default", "package/pkg-a", "package/pkg-b"]
