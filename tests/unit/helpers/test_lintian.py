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

"""Tests for debcraft's lintian helper."""

import pytest
from debcraft.helpers import lintian


@pytest.mark.parametrize("debian_dir", ["debian"])
@pytest.mark.parametrize(
    ("packages", "files"),
    [
        pytest.param(["fake-project"], ["lintian-overrides"], id="default"),
        pytest.param(["pkg1", "pkg2"], ["pkg1.lintian-overrides"], id="single"),
        pytest.param(
            ["pkg1", "pkg2"],
            ["pkg1.lintian-overrides", "pkg2.lintian-overrides"],
            id="both",
        ),
    ],
)
def test_run(tmp_path, default_project, debian_dir, packages, files):
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    install_dirs = {}
    for package in packages:
        partition = f"package/{package}"
        install_dirs[partition] = tmp_path / package / "install"
        install_dirs[partition].mkdir(parents=True, exist_ok=True)

    for file in files:
        file_path = build_dir / debian_dir / file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("content")

    helper = lintian.Lintian()
    helper.run(build_dir=build_dir, install_dirs=install_dirs, project=default_project)

    for package in packages:
        partition = f"package/{package}"
        lintian_dir = install_dirs[partition] / "usr/share/lintian/overrides"

        for lintian_file in files:
            if lintian_file == "lintian-overrides":
                package_from_lintian_file = default_project.name
            else:
                package_from_lintian_file = lintian_file.removesuffix(
                    ".lintian-overrides"
                )

            installed_lintian_file = lintian_dir / package_from_lintian_file

            if package == package_from_lintian_file:
                assert installed_lintian_file.exists()
                assert installed_lintian_file.read_bytes() == b"content"
            else:
                assert not installed_lintian_file.exists()
