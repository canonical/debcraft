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

import pytest
from debcraft.elf import ElfFile
from debcraft.helpers import makeshlibs


@pytest.mark.parametrize(
    ("arch", "create_files"),
    [
        pytest.param("s390x", True, id="native-arch"),
        pytest.param("riscv64", False, id="foreign-arch"),
    ],
)
def test_run(mocker, tmp_path, default_project, arch, create_files):
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
                path=prime_dir / "libfoo.so.5", libname="libfoo", ver="5", arch=arch
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

    shlibs_file = control_dir / "shlibs"
    triggers_file = control_dir / "triggers"

    if create_files:
        assert shlibs_file.read_text() == "libfoo 5 package-1 (>= 2.0)\n"
        assert triggers_file.read_text() == "activate-noawait ldconfig\n"
    else:
        assert not shlibs_file.exists()
        assert not triggers_file.exists()
