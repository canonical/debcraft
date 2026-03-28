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

"""Debcraft compress helper."""

import gzip
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

from craft_cli import emit

from .helpers import Helper

_COMPRESS_THRESHOLD = 4096


class Compress(Helper):
    """Debcraft compress helper."""

    def run(self, *, prime_dir: Path, **kwargs: Any) -> None:  # noqa: ARG002
        """Compress files in the given package.

        :param prime_dir: the directory containing the files to be stripped.
        """
        all_symlinks: list[Path] = []
        inode_map = defaultdict(list)

        for entry in prime_dir.rglob("*"):
            if entry.is_symlink():
                all_symlinks.append(entry)
            elif entry.is_file():
                inode_map[entry.lstat().st_ino].append(entry)

        compressed_files: set[Path] = set()

        for group in inode_map.values():
            if any(_should_compress(p, prime_dir) for p in group):
                _compress_group(group)
                compressed_files |= set(group)

        _fix_symlinks(all_symlinks, compressed_files, prime_dir)


def _compress_group(group: list[Path]) -> None:
    primary = group[0]
    primary_gz = primary.with_name(primary.name + ".gz")

    # Compress file
    with primary.open("rb") as f_in:
        with gzip.GzipFile(primary_gz, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    emit.progress(f"Compressed {primary_gz!s}")

    # Copy permissions/attributes (mode, atime, mtime)
    shutil.copystat(primary, primary_gz)

    # Handle hard links
    for path in group:
        gz_path = path.with_name(path.name + ".gz")

        # If this wasn't the primary file, link it to the primary .gz
        if path != primary:
            if gz_path.exists():
                gz_path.unlink()
            os.link(primary_gz, gz_path)

        # Remove the original uncompressed file
        path.unlink()


def _fix_symlinks(
    symlinks: list[Path], compressed_files: set[Path], root: Path
) -> None:
    for link in symlinks:
        target_path = Path.readlink(link)

        if target_path.is_absolute():
            search_path = root / target_path.relative_to("/")
        else:
            search_path = (link.parent / target_path).resolve()

        # Does this symlink point to a file we just compressed?
        if search_path in compressed_files:
            link.unlink()
            link_gz = link.parent / (link.name + ".gz")
            link_gz.symlink_to(target_path.name + ".gz")


def _should_compress(path: Path, root: Path) -> bool:
    rel_path = path.relative_to(root)

    # Hard Exclusions
    if path.name == "copyright":
        return False

    if path.suffix in {".gz", ".zip", ".pdf", ".png", ".jpg"}:
        return False

    # Mandatory Compression (man/info)
    if rel_path.is_relative_to("usr/share/man") or rel_path.is_relative_to(
        "usr/share/info"
    ):
        return True

    # Changelogs (Debian policy 12.7)
    # Matches: changelog, changelog.Debian, changelog.html, etc.
    if re.search(r"changelog(\..*)?$", path.name, re.IGNORECASE):
        return True

    # Compress documentation files > 4kb
    return (
        rel_path.is_relative_to("usr/share/doc")
        and path.stat().st_size > _COMPRESS_THRESHOLD
    )
