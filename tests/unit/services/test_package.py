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
"""Tests for debcraft's package service."""

import pytest
from debcraft import models
from debcraft.services import package


@pytest.fixture
def package_service_with_configured_project(
    project_service,
    package_service: package.Package,
) -> package.Package:
    project_service.configure(platform=None, build_for=None)
    return package_service


def test_pack(
    package_service_with_configured_project: package.Package,
    tmp_path,
    default_project: models.Project,
    host_architecture: str,
):
    package_service_with_configured_project.pack(
        prime_dir=tmp_path / "prime", dest=tmp_path
    )

    source_tarball = (
        tmp_path
        / f"{default_project.name}_{default_project.version}_{host_architecture}.tar.xz"
    )
    assert source_tarball.exists()


def test_generate_metadata(
    package_service_with_configured_project: package.Package,
    host_architecture: str,
):
    expected = models.Metadata(
        name="fake-project",
        version="1.0",
        architecture=host_architecture,
    )

    assert package_service_with_configured_project.metadata == expected
