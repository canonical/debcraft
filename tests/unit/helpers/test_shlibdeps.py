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

"""Tests for debcraft's shlibdeps helper."""

import pathlib
import textwrap

import pytest
from debcraft.elf import ElfFile, ElfLibrary
from debcraft.helpers import shlibdeps

_SHLIBS_CONTENT = "libssh2 1 libssh2-1t64 (>= 1.11.0)\n"

_SYMBOLS_CONTENT = textwrap.dedent(
    """\
    libssh2.so.1 libssh2-1t64 #MINVER#
    * Build-Depends-Package: libssh2-1-dev
     libssh2_agent_connect@Base 1.2.3
     libssh2_agent_get_identity_path@Base 1.9.0
     """
)


@pytest.fixture
def fake_library_map(mocker) -> shlibdeps._LibraryMap:
    libmap = mocker.MagicMock()
    libmap.soname_to_package = {"libssh2.so.1": "libssh2-1t64"}
    return libmap


def test_sonamemap_load_packaged_shlibs(mocker, tmp_path, fake_library_map):
    shlibs_file = tmp_path / "libssh2-1t64:amd64.shlibs"
    shlibs_file.write_text(_SHLIBS_CONTENT)

    soname_map = shlibdeps._SonameMap(fake_library_map)

    state_dir_map = {"package-name": tmp_path}
    soname_map.load_packaged_shlibs(state_dir_map)
    assert soname_map.get("libssh2.so.1") == "libssh2-1t64 (>= 1.11.0)"


def test_sonamemap_load_deb_info_shlibs(mocker, tmp_path, fake_library_map):
    shlibs_file = tmp_path / "libssh2-1t64:amd64.shlibs"
    shlibs_file.write_text(_SHLIBS_CONTENT)
    mocker.patch("debcraft.helpers.shlibdeps._DPKG_INFO_DIR", tmp_path)

    soname_map = shlibdeps._SonameMap(fake_library_map)

    soname_map.load_deb_info_shlibs("libssh2.so.1", "amd64")
    assert soname_map.get("libssh2.so.1") == "libssh2-1t64 (>= 1.11.0)"


def test_symbolsmap_from_deb_info_symbols(mocker, tmp_path, fake_library_map):
    symbols_file = tmp_path / "libssh2-1t64:amd64.symbols"
    symbols_file.write_text(_SYMBOLS_CONTENT)
    mocker.patch("debcraft.helpers.shlibdeps._DPKG_INFO_DIR", tmp_path)

    symbol_map = shlibdeps._SymbolMap(fake_library_map)

    symbol_map.load_deb_info_symbols("libssh2.so.1", "amd64")
    assert symbol_map.get(("libssh2.so.1", "libssh2_agent_connect@Base")) == (
        "libssh2-1t64",
        "1.2.3",
    )
    assert symbol_map.get(("libssh2.so.1", "libssh2_agent_get_identity_path@Base")) == (
        "libssh2-1t64",
        "1.9.0",
    )


def test_run(mocker, tmp_path):
    ef = ElfFile(
        path=pathlib.Path("/usr/bin/foo"),
        is_dynamic=True,
        arch="amd64",
        needed=[
            ElfLibrary("libfoo.so.2", "libfoo", "2"),
            ElfLibrary("libbar.so.1", "libbar", "1"),
        ],
    )

    mocker.patch(
        "debcraft.elf.elf_file._read_undefined_symbols",
        return_value={"foo_init@Base", "bar_init@Base", "bar_run@Base"},
    )
    mocker.patch("debcraft.helpers.shlibdeps._DPKG_INFO_DIR", tmp_path)
    mocker.patch("debcraft.helpers.shlibdeps.get_elf_files", return_value=[ef])
    fake_libmap = mocker.patch("debcraft.helpers.shlibdeps._LibraryMap")
    fake_libmap.return_value.soname_to_package = {
        "libfoo.so.2": "libfoo2",
        "libbar.so.1": "libbar1",
    }

    # libfoo only has a .shlibs file
    libfoo_shlibs = tmp_path / "libfoo2:amd64.shlibs"
    libfoo_shlibs.write_text("libfoo 2 libfoo2-1t64 (>= 2.1.0)\n")

    # libbar has both .shlibs and .symbols files
    libbar_shlibs = tmp_path / "libbar1:amd64.shlibs"
    libbar_shlibs.write_text("libbar 1 libbar1 (>= 1.1.0)\n")
    libbar_symbols = tmp_path / "libbar1:amd64.symbols"
    libbar_symbols.write_text(
        textwrap.dedent(
            """\
        libbar.so.1 libbar1 #MINVER#
        * Build-Depends-Package: libbar-dev
         bar_init@Base 1.0.0
         bar_run@Base 1.0.5
        """
        )
    )

    prime_dir = tmp_path / "prime"
    prime_dir.mkdir()

    helper = shlibdeps.Shlibdeps()
    helper.run(
        package_name="pkgname",
        arch="amd64",
        prime_dir=prime_dir,
        state_dir=tmp_path,
        state_dir_map={"pkgname": tmp_path},
    )

    shlibs_file = tmp_path / "shlibdeps"
    shlibs = shlibs_file.read_text()
    assert shlibs == "libbar1 (>= 1.0.5)\nlibfoo2-1t64 (>= 2.1.0)\n"
