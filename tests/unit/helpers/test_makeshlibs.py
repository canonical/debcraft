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

"""Tests for debcraft's makeshlibs helper."""

from debcraft.elf import ElfFile
from debcraft.helpers import makeshlibs


def test_run(mocker, tmp_path, default_project):
    prime_dir = tmp_path / "prime"
    control_dir = tmp_path / "control"
    state_dir = tmp_path / "state"

    prime_dir.mkdir()
    control_dir.mkdir()
    state_dir.mkdir()

    mocker.patch(
        "debcraft.helpers.makeshlibs.get_elf_files",
        return_value=[
            ElfFile(
                path=prime_dir / "libfoo.so.5", libname="libfoo", ver="5", arch="s390x"
            )
        ],
    )

    helper = makeshlibs.Makeshlibs()
    helper.run(
        prime_dir=prime_dir,
        control_dir=control_dir,
        state_dir=state_dir,
        project=default_project,
        arch="s390x",
        package_name="package-1",
    )

    content = (control_dir / "shlibs").read_text()
    assert content == "libfoo 5 package-1 (>= 2.0)\n"
