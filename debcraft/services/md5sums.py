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

"""Debcraft md5sums helper service."""

import hashlib
import pathlib

from .helper import HelperService


class Md5sumsService(HelperService):
    """Debcraft md5sums helper service.

    The md5sums helper will:
    - Scan prime dir for files
    - Create a md5sums file listing the MD5 digests and files
    """

    def run(self, root: pathlib.Path, dest_dir: pathlib.Path) -> None:
        """Walk subtree and write md5 checksums with relative paths."""
        output_file = dest_dir / "md5sums"
        with output_file.open("w") as out:
            for file in root.rglob("*"):
                if file.is_file():
                    checksum = _md5sum(file)
                    relpath = file.relative_to(root)
                    out.write(f"{checksum}  {relpath}\n")


def _md5sum(path: pathlib.Path) -> str:
    """Compute MD5 checksum of a file."""
    h = hashlib.md5()  # noqa: S324
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
