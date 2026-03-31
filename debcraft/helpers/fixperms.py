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

"""Debcraft fixperms helper."""

import fnmatch
import os
import pathlib
from typing import Any

from craft_cli import emit

from .helpers import Helper

# Patterns from dh_fixperms
_MODE_0644_PATTERNS = (
    # Libraries and related files
    "*.so.*",
    "*.so",
    "*.la",
    "*.a",
    # Web application related files
    "*.js",
    "*.css",
    "*.scss",
    "*.sass",
    # Images
    "*.jpeg",
    "*.jpg",
    "*.png",
    "*.gif",
    # OCaml native-code shared objects
    "*.cmxs",
    # Node bindings
    "*.node",
)

_MODE_0644_PATHS = (
    "usr/share/doc",
    "usr/share/man",
    "usr/share/applications",
    "usr/include",
    "usr/share/lintian/overrides",
)

_MODE_0755_PATHS = (
    "usr/bin",
    "bin",
    "usr/sbin",
    "sbin",
    "usr/games",
    "etc/init.d",
    "usr/libexec",
)

_MODE_0755_NODEJS_PATTERNS = (
    "usr/lib/nodejs/*/cli.js",
    "usr/lib/nodejs/*/bin.js",
)


class Fixperms(Helper):
    """Debcraft fixperms helper."""

    def run(self, *, prime_dir: pathlib.Path, **kwargs: Any) -> None:  # noqa: ARG002
        """Fix file permissions.

        :param prime_dir: the directory containing the files to be packaged.
        """
        for entry in prime_dir.rglob("*"):
            if entry.is_symlink():
                os.lchown(entry, 0, 0)
                continue

            os.chown(entry, 0, 0)

            if entry.is_dir():
                entry.chmod(0o755)
            elif entry.is_file():
                rel_path = entry.relative_to(prime_dir)
                mode = entry.stat().st_mode & 0o7777
                new_mode = _get_normalized_file_mode(rel_path)
                if mode != new_mode:
                    emit.debug(
                        f"fixperms: change {rel_path!s} permissions from {mode:0>3o} to {new_mode:0>3o}"
                    )
                    entry.chmod(new_mode)


def _get_normalized_file_mode(rel_path: pathlib.Path) -> int:
    filename = rel_path.name

    if any(fnmatch.fnmatch(rel_path.as_posix(), p) for p in _MODE_0755_NODEJS_PATTERNS):
        return 0o755

    if any(fnmatch.fnmatch(filename, p) for p in _MODE_0644_PATTERNS):
        return 0o644

    if any(rel_path.is_relative_to(p) for p in _MODE_0644_PATHS):
        return 0o644

    if any(rel_path.is_relative_to(p) for p in _MODE_0755_PATHS):
        return 0o755

    if rel_path.is_relative_to("etc/sudoers.d"):
        return 0o440

    return 0o644
