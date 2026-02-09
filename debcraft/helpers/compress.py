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

import fnmatch
import gzip
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

from craft_cli import emit

from .helpers import Helper

_COMPRESS_THRESHOLD = 4096

# Exclusion patterns from dh_compress

# Exclude from usr/share/info and usr/share/man
_EXCLUDE_INFO_MAN = ("*.gz", "*.gif", "*.png", "*.jpg", "*.jpeg")

# Exclude from usr/share/doc
_EXCLUDE_DOC = (
    "*.htm*",
    "*.xhtml",
    "*.gif",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gz",
    "*.taz",
    "*.tgz",
    "*.z",
    "*.bz2",
    "*-gz",
    "*-z",
    "*_z",
    "*.epub",
    "*.jar",
    "*.zip",
    "*.odg",
    "*.odp",
    "*.odt",
    ".htaccess",
    "*.css",
    "*.xz",
    "*.lz",
    "*.lzma",
    "*.haddock",
    "*.hs",
    "*.svg",
    "*.svgz",
    "*.js",
    "index.sgml",
    "objects.inv",
    "*.map",
    "*.devhelp2",
    "search_index.json",
    "copyright",
    "*.pdf",
)

# Exclude from usr/share/fonts/X11
_EXCLUDE_FONTS_X11 = ("*.pcf",)


class Compress(Helper):
    """Debcraft compress helper."""

    def run(self, *, prime_dir: Path, **kwargs: Any) -> None:  # noqa: ARG002
        """Compress eligible files in the given package.

        :param prime_dir: the directory containing the files to be compressed.
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
            if all(_should_compress(p, prime_dir) for p in group):
                _compress_group(group, prime_dir)
                compressed_files |= set(group)

        _fix_symlinks(all_symlinks, compressed_files, prime_dir)


def _compress_group(group: list[Path], prime_dir: Path) -> None:
    primary = group[0]
    primary_gz = primary.with_name(primary.name + ".gz")
    mtime = _get_mtime(primary)

    # Compress file
    with primary.open("rb") as f_in:
        with gzip.GzipFile(primary_gz, "wb", mtime=mtime) as f_out:
            shutil.copyfileobj(f_in, f_out)

    emit.progress(f"Compress file: {primary_gz.relative_to(prime_dir)!s}")

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
        if not link.is_symlink():
            continue

        target_path = Path.readlink(link)
        if target_path.is_absolute():
            search_path = root / target_path.relative_to("/")
        else:
            search_path = (link.parent / target_path).resolve()

        # Does this symlink point to a file we just compressed?
        if search_path in compressed_files:
            link.unlink()
            link_gz = link.parent / (link.name + ".gz")
            target_gz = target_path.parent / (target_path.name + ".gz")
            link_gz.symlink_to(target_gz)
            emit.progress(
                f"Fix symlink: {link_gz.relative_to(root)!s} -> {target_gz!s}"
            )
            remaining_symlinks = [s for s in symlinks if s != link]
            if remaining_symlinks:
                _fix_symlinks(
                    remaining_symlinks,
                    (compressed_files - {search_path}) | {link},
                    root,
                )


def _should_compress(path: Path, root: Path) -> bool:
    rel_path = path.relative_to(root)

    if rel_path.is_relative_to("usr/share/man") or rel_path.is_relative_to(
        "usr/share/info"
    ):
        return not any(fnmatch.fnmatch(path.name, p) for p in _EXCLUDE_INFO_MAN)

    if rel_path.is_relative_to("usr/share/doc"):
        if fnmatch.fnmatch(path.name.lower(), "changelog*") or fnmatch.fnmatch(
            path.name, "NEWS*"
        ):
            return True

        if path.stat().st_size <= _COMPRESS_THRESHOLD:
            return False

        return not any(fnmatch.fnmatch(path.name, p) for p in _EXCLUDE_DOC)

    if rel_path.is_relative_to("usr/share/fonts/X11"):
        return not any(fnmatch.fnmatch(path.name, p) for p in _EXCLUDE_FONTS_X11)

    return False


def _get_mtime(file: Path) -> int:
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch:
        try:
            return int(source_date_epoch)
        except ValueError:
            return int(file.stat().st_mtime)

    return int(file.stat().st_mtime)
