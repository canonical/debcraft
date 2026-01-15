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

"""Tests for ELF file helpers."""

import shutil

from debcraft.elf import elf_utils


def test_get_elf_files_recursive(tmp_path):
    shutil.copy("/bin/true", tmp_path)
    shutil.copy("/etc/issue", tmp_path)
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    shutil.copy("/bin/false", subdir)

    elf_files = elf_utils.get_elf_files(tmp_path)
    assert len(elf_files) == 2
    assert elf_files[0].path == tmp_path / "true"
    assert elf_files[1].path == tmp_path / "subdir" / "false"


def test_get_elf_files_non_recursive(tmp_path):
    shutil.copy("/bin/true", tmp_path)
    shutil.copy("/etc/issue", tmp_path)
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    shutil.copy("/bin/false", subdir)

    elf_files = elf_utils.get_elf_files(tmp_path, recursive=False)
    assert len(elf_files) == 1
    assert elf_files[0].path == tmp_path / "true"
