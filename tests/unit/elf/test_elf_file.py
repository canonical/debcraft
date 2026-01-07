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

import pytest
import pytest_mock
from craft_application.util import get_host_architecture
from debcraft import errors, util
from debcraft.elf import ElfFile, ElfLibrary
from debcraft.elf.elf_file import _get_elf_debian_arch
from elftools.elf import elffile


def _lib_triplet() -> pathlib.Path:
    return pathlib.Path("/usr/lib") / util.get_arch_triplet()


@pytest.mark.parametrize(
    ("filename", "soname", "ver", "needed"),
    [
        (_lib_triplet() / "libdl.so.2", "libdl", "2", {ElfLibrary("libc", "6")}),
        ("/bin/gzip", "", "", {ElfLibrary("libc", "6")}),
    ],
)
def test_elf_file(filename: str, soname: str, ver: str, needed: set[ElfLibrary]):
    path = pathlib.Path(filename)
    assert ElfFile.is_elf(path)

    elf_file = ElfFile.from_path(path)
    assert elf_file.path == path
    assert elf_file.arch == get_host_architecture()
    assert elf_file.soname == soname
    assert elf_file.ver == ver
    assert elf_file.needed == needed


def test_elf_file_not_elf():
    path = pathlib.Path("/etc/issue")
    assert not ElfFile.is_elf(path)

    with pytest.raises(errors.DebcraftError) as raised:
        ElfFile.from_path(path)

    err = str(raised.value)
    assert err == "cannot load ELF file: Magic number does not match"


@pytest.mark.parametrize(
    ("filename", "soname", "ver"),
    [
        ("libfoo.so.123", "libfoo", "123"),
        ("libbar.so", "libbar.so", ""),
        ("", "", ""),
    ],
)
def test_elf_library(filename: str, soname: str, ver: str):
    lib = ElfLibrary.from_name(filename)
    assert lib.soname == soname
    assert lib.ver == ver


@pytest.mark.parametrize(
    ("e_machine", "ei_class", "ei_data", "arch"),
    [
        ("EM_X86_64", "ELFCLASS64", "ELFDATA2LSB", "amd64"),
        ("EM_386", "ELFCLASS32", "ELFDATA2LSB", "i386"),
        ("EM_AARCH64", "ELFCLASS64", "ELFDATA2LSB", "arm64"),
        ("EM_ARM", "ELFCLASS32", "ELFDATA2LSB", "armhf"),
        ("EM_PPC64", "ELFCLASS64", "ELFDATA2LSB", "ppc64el"),
        ("EM_PPC64", "ELFCLASS64", "ELFDATA2MSB", "ppc64"),
        ("EM_MIPS", "ELFCLASS32", "ELFDATA2LSB", "mipsel"),
        ("EM_MIPS", "ELFCLASS32", "ELFDATA2MSB", "mips"),
        ("EM_S390", "ELFCLASS64", "ELFDATA2MSB", "s390x"),
        ("EM_RISCV", "ELFCLASS64", "ELFDATA2LSB", "riscv64"),
        ("other", "ELFCLASS64", "ELFDATA2LSB", "unknown"),
        ("EM_X86_64", "other", "ELFDATA2LSB", "unknown"),
        ("EM_X86_64", "ELFCLASS64", "other", "unknown"),
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
