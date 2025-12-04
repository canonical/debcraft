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

"""Debian control file encoder."""

from typing import TextIO

from debcraft import models


class Encoder:
    """Encoder for Debian control file format."""

    def __init__(self, f: TextIO) -> None:
        self._file = f

    def encode(self, model: models.DebianBinaryPackageControl) -> None:
        """Encode the model."""
        for name, field in model.__class__.model_fields.items():
            value = getattr(model, name)
            if value is None:
                continue

            key = field.alias or name

            match value:
                case str() if "\n" in value:
                    lines = value.splitlines()
                    self._file.write(f"{key}: {lines[0]}\n")
                    for line in lines[1:]:
                        if line.strip() == "":
                            self._file.write(" .\n")
                        else:
                            self._file.write(f" {line}\n")
                case list():
                    line = ", ".join(map(str, value))  # pyright: ignore[reportUnknownVariableType,reportUnknownArgumentType]
                    self._file.write(f"{key}: {line}\n")
                case _:
                    self._file.write(f"{key}: {value}\n")
