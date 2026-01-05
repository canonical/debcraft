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

"""ELF file handling errors."""

from pathlib import Path

from debcraft import errors


class CorruptedElfFile(errors.DebcraftError):
    """Not a valid ELF file."""

    def __init__(self, path: Path, error: Exception) -> None:
        self.path = path

        super().__init__(f"Error parsing ELF file {str(path)!r}: {str(error)}")


class DynamicLinkerNotFound(errors.DebcraftError):
    """Failed to find the dynamic linker for this platform."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Dynamic linker {str(path)!r} not found.")
