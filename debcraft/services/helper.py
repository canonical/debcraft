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

"""Debcraft base helper service."""

from typing import cast

from craft_application import ProjectService

from debcraft.elf import ElfFile, elf_utils

from .lifecycle import Lifecycle


class HelperService(ProjectService):
    """Debcraft base helper Service."""

    def _get_primed_elf_files(self, package: str) -> list[ElfFile]:
        """Obtain a set of all primed ELF files in a giving package.

        :param package: the name of the deb package containing the
            installed files.
        :return: the list of installed ELF files.
        """
        prime_dir = cast(Lifecycle, self._services.get("lifecycle")).get_prime_dir(
            package
        )

        return elf_utils.get_elf_files(prime_dir)
