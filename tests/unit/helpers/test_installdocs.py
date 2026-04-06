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

"""Tests for debcraft's installdocs helper."""

import pytest
from debcraft.helpers import installdocs


@pytest.mark.parametrize("debian_dir", ["debcraft", "debian"])
@pytest.mark.parametrize(
    ("packages", "files", "docs"),
    [
        pytest.param(["pkg1"], ["not-copyright"], [], id="other"),
        pytest.param(["pkg1", "pkg2"], ["copyright"], ["copyright"], id="copyright"),
    ],
)
def test_run(tmp_path, default_project, debian_dir, packages, files, docs):
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

    helper = installdocs.Installdocs()
    helper.run(build_dir=build_dir, install_dirs=install_dirs, project=default_project)

    for package in packages:
        partition = f"package/{package}"
        doc_dir = install_dirs[partition] / "usr/share/doc" / package

        if not docs:
            assert not doc_dir.exists()
            continue

        for doc in docs:
            doc_file = doc_dir / doc
            assert doc_file.exists()
            assert doc_file.read_bytes() == b"content"
