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
    ("arch", "create_files", "pkg_version", "expected_version"),
    [
        pytest.param("s390x", True, "2.0", "2.0", id="native-arch"),
        pytest.param("riscv64", False, "2.0", "2.0", id="foreign-arch"),
        pytest.param(
            "s390x", True, "2.0-1ubuntu5", "2.0", id="native-arch-with-revision"
        ),
    ],
)
def test_run(
    mocker, tmp_path, default_project, arch, create_files, pkg_version, expected_version
):
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
    mocker.patch(
        "debcraft.models.project.Project.get_package",
        return_value=mocker.MagicMock(version=pkg_version),
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
        assert (
            shlibs_file.read_text() == f"libfoo 5 package-1 (>= {expected_version})\n"
        )
        assert triggers_file.read_text() == "activate-noawait ldconfig\n"
    else:
        assert not shlibs_file.exists()
        assert not triggers_file.exists()


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        pytest.param("1.0.0", "1.0.0", id="no-revision"),
        pytest.param("1.0.0-1", "1.0.0", id="simple-debian-revision"),
        pytest.param("12.0.0-1ubuntu5", "12.0.0", id="ubuntu-revision"),
        pytest.param("2:1.0.0-1", "2:1.0.0", id="epoch-with-revision"),
        pytest.param("2:1.0.0", "2:1.0.0", id="epoch-no-revision"),
        pytest.param("1.0.0-1-2", "1.0.0-1", id="upstream-version-contains-hyphen"),
        pytest.param(
            "12.0.0-1ubuntu5~", "12.0.0-1ubuntu5~", id="revision-tilde-backport"
        ),
        pytest.param("12.0.0~rc1-1", "12.0.0~rc1", id="upstream-tilde-with-revision"),
        pytest.param(
            "12.0.0~rc1-1ubuntu5~",
            "12.0.0~rc1-1ubuntu5~",
            id="upstream-tilde-revision-tilde",
        ),
    ],
)
def test_get_shlibs_friendly_version(version: str, expected: str) -> None:
    assert makeshlibs.Makeshlibs._get_shlibs_friendly_version(version) == expected
