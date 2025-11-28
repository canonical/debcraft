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

import subprocess
from pathlib import Path

import craft_platforms
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


def _list_ar_members(ar_path: Path) -> list[str]:
    """Return the list of members in an ar archive."""
    result = subprocess.run(
        ["ar", "t", str(ar_path)], check=True, capture_output=True, text=True
    )
    return result.stdout.strip().splitlines()


def test_pack(
    package_service_with_configured_project: package.Package,
    tmp_path,
    default_project: models.Project,
    host_architecture: str,
):
    prime_dir = tmp_path / "work" / "partitions" / "package" / "package-1" / "prime"
    prime_dir.mkdir(exist_ok=True, parents=True)
    (prime_dir / "foo.txt").touch()
    package_service_with_configured_project.pack(prime_dir=prime_dir, dest=tmp_path)

    deb_file = tmp_path / f"package-1_2.0_{host_architecture}.deb"
    assert deb_file.exists()

    members = _list_ar_members(deb_file)
    assert members == ["debian-binary", "control.tar.zst", "data.tar.zst"]


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
    arch = package._get_architecture(pkg, info)
    assert arch == binary_arch


def test_md5sum(tmp_path):
    foo = tmp_path / "foo.txt"
    foo.write_text("file content")
    result = package._md5sum(foo)
    assert result == "d10b4c3ff123b26dc068d43a8bef2d23"


def test_create_md5sums(tmp_path):
    test_dir = tmp_path / "dir"
    test_dir.mkdir()
    foo = test_dir / "foo.txt"
    bar = test_dir / "bar.txt"
    foo.write_text("file content")
    bar.write_text("more file content")
    package._create_md5sums(test_dir, tmp_path / "md5sums")

    content = (tmp_path / "md5sums").read_text()
    assert "cc4005f23a42e90094a943e9eb5cbce3  bar.txt\n" in content
    assert "d10b4c3ff123b26dc068d43a8bef2d23  foo.txt\n" in content
