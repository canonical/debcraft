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

import pathlib
import platform

import pytest
import pytest_mock
from craft_application.util import get_host_architecture
from debcraft import errors, util
from debcraft.elf import ElfFile, ElfLibrary
from debcraft.elf.elf_file import _get_elf_debian_arch
from elftools.elf import elffile

if platform.machine() == "aarch64":
    EXTRA_LIBRARY = {ElfLibrary("ld-linux-aarch64", "1")}
else:
    EXTRA_LIBRARY = set()


def _lib_triplet() -> pathlib.Path:
    return pathlib.Path("/usr/lib") / util.get_arch_triplet()


@pytest.mark.parametrize(
    ("filename", "libname", "ver", "needed"),
    [
        pytest.param(
            _lib_triplet() / "libdl.so.2",
            "libdl",
            "2",
            {ElfLibrary("libc", "6")},
            id="with_library",
        ),
        pytest.param(
            "/bin/gzip",
            "",
            "",
            {ElfLibrary("libc", "6")} | EXTRA_LIBRARY,
            id="with_binary",
        ),
    ],
)
def test_elf_file(filename: str, libname: str, ver: str, needed: set[ElfLibrary]):
    path = pathlib.Path(filename)
    assert ElfFile.is_elf(path)

    elf_file = ElfFile.from_path(path)
    assert elf_file.path == path
    assert elf_file.arch == get_host_architecture()
    assert elf_file.libname == libname
    assert elf_file.ver == ver
    assert elf_file.needed == needed


def test_elf_file_not_elf():
    path = pathlib.Path("/etc/issue")
    assert not ElfFile.is_elf(path)

    with pytest.raises(errors.DebcraftError, match="Magic number does not match"):
        ElfFile.from_path(path)


@pytest.mark.parametrize(
    ("filename", "libname", "ver"),
    [
        pytest.param("libfoo.so.123", "libfoo", "123", id="with_so_ver_suffix"),
        pytest.param("libbar.so", "libbar.so", "", id="with_so_suffix"),
        pytest.param("", "", "", id="empty"),
    ],
)
def test_elf_library(filename: str, libname: str, ver: str):
    lib = ElfLibrary.from_name(filename)
    assert lib.libname == libname
    assert lib.ver == ver


@pytest.mark.parametrize(
    ("e_machine", "ei_class", "ei_data", "arch"),
    [
        pytest.param("EM_X86_64", "ELFCLASS64", "ELFDATA2LSB", "amd64", id="amd64"),
        pytest.param("EM_386", "ELFCLASS32", "ELFDATA2LSB", "i386", id="i386"),
        pytest.param("EM_AARCH64", "ELFCLASS64", "ELFDATA2LSB", "arm64", id="arm64"),
        pytest.param("EM_ARM", "ELFCLASS32", "ELFDATA2LSB", "armhf", id="armhf"),
        pytest.param("EM_PPC64", "ELFCLASS64", "ELFDATA2LSB", "ppc64el", id="ppc64el"),
        pytest.param("EM_PPC64", "ELFCLASS64", "ELFDATA2MSB", "ppc64", id="ppc64"),
        pytest.param("EM_MIPS", "ELFCLASS32", "ELFDATA2LSB", "mipsel", id="mipsel"),
        pytest.param("EM_MIPS", "ELFCLASS32", "ELFDATA2MSB", "mips", id="mips"),
        pytest.param("EM_S390", "ELFCLASS64", "ELFDATA2MSB", "s390x", id="s390x"),
        pytest.param("EM_RISCV", "ELFCLASS64", "ELFDATA2LSB", "riscv64", id="riscv64"),
        pytest.param("x", "ELFCLASS64", "ELFDATA2LSB", "unknown", id="machine_unknown"),
        pytest.param("EM_X86_64", "x", "ELFDATA2LSB", "unknown", id="class_unknown"),
        pytest.param("EM_X86_64", "ELFCLASS64", "x", "unknown", id="arch_unknown"),
    ],
)
def test_get_elf_debian_arch(
    mocker: pytest_mock.MockerFixture,
    e_machine: str,
    ei_class: str,
    ei_data: str,
    arch: str,
):
    elf_file = mocker.MagicMock(spec=elffile.ELFFile)
    elf_file.header = {
        "e_machine": e_machine,
        "e_ident": {
            "EI_CLASS": ei_class,
            "EI_DATA": ei_data,
        },
    }

    debian_arch = _get_elf_debian_arch(elf_file)
    assert debian_arch == arch
