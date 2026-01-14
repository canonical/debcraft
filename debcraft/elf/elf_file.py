#  This file is part of debcraft.
#
#  Copyright 2016-2025 Canonical Ltd.
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

"""Helpers to parse and handle ELF binary files."""

import pathlib
from dataclasses import dataclass, field

from elftools.common.exceptions import ELFError
from elftools.elf import dynamic, elffile
from typing_extensions import Self

from debcraft import errors


@dataclass(frozen=True)
class ElfLibrary:
    """Representation of an ELF dynamic library."""

    soname: str
    ver: str

    @classmethod
    def from_name(cls, name: str) -> Self:
        """Create a ElfLibrary instance from a shared library name.

        :param name: The shared library name.

        :return: A newly created ElfLibrary instance.
        """
        if ".so." not in name:
            return cls(soname=name, ver="")

        soname, ver = name.split(".so.", maxsplit=1)
        return cls(soname, ver)


@dataclass(frozen=True)
class ElfSymbol:
    """Representation of an ELF symbol."""

    name: str
    minver: str


@dataclass
class ElfFile:
    """ELF files."""

    path: pathlib.Path
    is_dynamic: bool = False
    soname: str = ""
    ver: str = ""
    arch: str = ""
    needed: set[ElfLibrary] = field(default_factory=set)
    symbols: set[ElfSymbol] = field(default_factory=set)

    @classmethod
    def is_elf(cls, path: pathlib.Path) -> bool:
        """Determine whether the given file is an ELF file.

        :param path: Path to the file to be verified.
        """
        if not path.is_file():
            return False

        with path.open("rb") as file:
            return file.read(4) == b"\x7fELF"

    @classmethod
    def from_path(cls, path: pathlib.Path) -> Self:
        """Represent the given file as an ElfFile.

        :param path: The path of the file to represent.

        :return: A newly created ElfFile instance.
        """
        with path.open("rb") as file:
            try:
                elf_file = elffile.ELFFile(file)
            except ELFError as err:
                raise errors.DebcraftError(f"cannot load ELF file: {err}")

            elf_data = cls(path=path)
            elf_data.arch = _get_elf_debian_arch(elf_file)

            dynamic_section = None
            for section in elf_file.iter_sections():
                if isinstance(section, dynamic.DynamicSection):
                    dynamic_section = section
                    break

            if not dynamic_section:
                return elf_data

            elf_data.is_dynamic = True
            for tag in dynamic_section.iter_tags():
                if tag.entry.d_tag == "DT_NEEDED":
                    needed = tag.needed  # pyright: ignore[reportAttributeAccessIssue]
                    if ".so." in needed:
                        elf_data.needed.add(ElfLibrary.from_name(needed))
                elif tag.entry.d_tag == "DT_SONAME":
                    soname = tag.soname  # pyright: ignore[reportAttributeAccessIssue]
                    elf_lib = ElfLibrary.from_name(soname)
                    elf_data.soname = elf_lib.soname
                    elf_data.ver = elf_lib.ver

        return elf_data


_ELF_ARCH_MAP = {
    ("EM_X86_64", "ELFCLASS64", "ELFDATA2LSB"): "amd64",
    ("EM_386", "ELFCLASS32", "ELFDATA2LSB"): "i386",
    ("EM_AARCH64", "ELFCLASS64", "ELFDATA2LSB"): "arm64",
    ("EM_ARM", "ELFCLASS32", "ELFDATA2LSB"): "armhf",
    ("EM_PPC64", "ELFCLASS64", "ELFDATA2LSB"): "ppc64el",
    ("EM_PPC64", "ELFCLASS64", "ELFDATA2MSB"): "ppc64",
    ("EM_MIPS", "ELFCLASS32", "ELFDATA2LSB"): "mipsel",
    ("EM_MIPS", "ELFCLASS32", "ELFDATA2MSB"): "mips",
    ("EM_S390", "ELFCLASS64", "ELFDATA2MSB"): "s390x",
    ("EM_RISCV", "ELFCLASS64", "ELFDATA2LSB"): "riscv64",
}


def _get_elf_debian_arch(elf_file: elffile.ELFFile) -> str:
    machine = elf_file.header["e_machine"]
    ei_class = elf_file.header["e_ident"]["EI_CLASS"]
    ei_data = elf_file.header["e_ident"]["EI_DATA"]

    return _ELF_ARCH_MAP.get((machine, ei_class, ei_data), "unknown")
