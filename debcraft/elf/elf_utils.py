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

"""Helpers to handle ELF files."""

import pathlib

from elftools.common.exceptions import ELFError

from .elf_file import ElfFile


def get_elf_files(path: pathlib.Path, *, recursive: bool = True) -> list[ElfFile]:
    """Obtain a list of all ELF files in a directory or subtree.

    :param root_path: The root of the subtree to list ELF files from.
    :param recursive: Whether this will be a recursive search.

    :return: A list of ELF files found in the given directory or subtree.
    """
    file_list: list[ElfFile] = []

    if not path.is_dir():
        return file_list

    files_to_check = path.rglob("*") if recursive else path.iterdir()

    for file in files_to_check:
        if not file.is_file():
            continue

        if file.suffix == ".o":
            continue

        if not ElfFile.is_elf(file):
            continue

        try:
            elf_file = ElfFile.from_path(path=file)
        except ELFError:
            # Ignore invalid ELF files.
            continue

        # If ELF has dynamic symbols, add it.
        if elf_file.is_dynamic:
            file_list.append(elf_file)

    return file_list
