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

"""Tests for debcraft's strip helper."""

from unittest.mock import call

from debcraft.elf import ElfFile
from debcraft.helpers import strip


def test_run(mocker, tmp_path):
    fake_subprocess_run = mocker.patch("subprocess.run")

    install_dir = tmp_path / "install"
    install_dir.mkdir()
    mocker.patch(
        "debcraft.elf.elf_utils.get_elf_files",
        return_value=[ElfFile(path=install_dir / "foo")],
    )

    helper = strip.Strip()
    helper.run(install_dir=install_dir)

    assert fake_subprocess_run.mock_calls == [
        call(["strip", "--strip-unneeded", install_dir / "foo"], check=True)
    ]
