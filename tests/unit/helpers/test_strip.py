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
    # The helper reads the files' permission bits, so they must exist.
    exe = install_dir / "foo"
    exe.touch()
    exe.chmod(0o755)
    lib = install_dir / "libfoo.so"
    lib.touch()
    lib.chmod(0o644)
    mocker.patch(
        "debcraft.elf.elf_utils.get_elf_files",
        return_value=[ElfFile(path=exe), ElfFile(path=lib)],
    )

    helper = strip.Strip()
    helper.run(install_dir=install_dir)

    assert fake_subprocess_run.mock_calls == [
        call(
            [
                "strip",
                "--remove-section=.comment",
                "--remove-section=.note",
                exe,
            ],
            check=True,
        ),
        call(
            [
                "strip",
                "--remove-section=.comment",
                "--remove-section=.note",
                "--strip-unneeded",
                lib,
            ],
            check=True,
        ),
    ]
