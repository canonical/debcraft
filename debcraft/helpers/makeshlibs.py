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

"""Debcraft makeshlibs helper service."""

import functools
import pathlib
import shutil
import subprocess
from typing import Any, cast

from craft_cli import emit

from debcraft import models, util
from debcraft.elf import get_elf_files

from .helpers import Helper


class Makeshlibs(Helper):
    """Debcraft makeshlibs helper.

    The makeshlibs helper will:
    - Scan prime dir for ELF shared libraries
    - Create a shlibs file listing the shared libraries
    """

    def run(
        self,
        *,
        prime_dir: pathlib.Path,
        control_dir: pathlib.Path,
        state_dir: pathlib.Path,
        project: models.Project,
        package_name: str,
        arch: str,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Create a list of shared libraries present in this package."""
        shlibs_file = control_dir / "shlibs"
        package = project.get_package(package_name)
        version = cast(str, package.version or project.version)
        arch_triplet = util.get_arch_triplet()
        lib_dirs = _get_lib_dirs(arch_triplet)

        primed_elf_files = []
        for lib_dir in lib_dirs:
            primed_elf_files.extend(
                get_elf_files(prime_dir / lib_dir.lstrip("/"), recursive=False)
            )

        primed_shlibs = [x for x in primed_elf_files if x.soname and x.ver]

        if not primed_shlibs:
            emit.debug(f"no primed shlibs in package {package_name}")
            return

        # Write shlibs file
        dedup: set[tuple[str, str]] = set()
        with shlibs_file.open("w", encoding="utf-8") as f:
            for elf in primed_shlibs:
                if elf.arch != arch:
                    continue

                # Deduplicate multiple occurences of the same library
                if (elf.soname, elf.ver) in dedup:
                    continue

                dedup.add((elf.soname, elf.ver))
                emit.progress(
                    f"Shared library in {package_name}: {elf.soname}.so.{elf.ver}"
                )
                f.write(f"{elf.soname} {elf.ver} {package_name} (>= {version})\n")

        # Copy to helper state
        state_shlibs_file = state_dir / f"{package_name}:{arch}.shlibs"
        shutil.copy(shlibs_file, state_shlibs_file)


@functools.lru_cache
def _get_lib_dirs(arch_triplet: str) -> list[str]:
    """Obtain a list of paths used by the dynamic linker to find libraries."""
    lib_dirs = {
        "/lib",
        "/usr/lib",
        f"/lib/{arch_triplet}",
        f"/usr/lib/{arch_triplet}",
        "/usr/local/lib",
    }

    output = subprocess.check_output(
        ["ldconfig", "-vNX"], stderr=subprocess.DEVNULL
    ).decode()
    for line in output.splitlines():
        if line.startswith("/"):
            lib_dirs.add(line.split(":")[0].strip())

    return sorted(lib_dirs)
