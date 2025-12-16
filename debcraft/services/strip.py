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

"""Debcraft strip helper service."""

import pathlib
import subprocess
from typing import Any

from craft_cli import emit

from debcraft import errors
from debcraft.elf import elf_utils

from .helper import HelperService


class StripService(HelperService):
    """Debcraft strip helper service.

    The strip helper will:
    - Scan prime dir for ELF files
    - Split debug symbols into separate debug packages (not currently implemented)
    - Call the strip tool on the primed ELF files
    """

    def run(self, *, prime_dir: pathlib.Path, **kwargs: Any) -> None:  # noqa: ARG002
        """Strip primed files in the given package.

        :param prime_dir: the directory containing the files to be stripped.
        """
        primed_elf_files = elf_utils.get_elf_files(prime_dir)

        for elf_file in primed_elf_files:
            try:
                emit.progress(f"Strip binary: {elf_file.path!s}")
                subprocess.run(["strip", "--strip-unneeded", elf_file.path], check=True)
            except subprocess.CalledProcessError as error:  # noqa: PERF203
                raise errors.DebcraftError(
                    f"cannot strip {str(elf_file.path)}", details=error.stderr
                )
