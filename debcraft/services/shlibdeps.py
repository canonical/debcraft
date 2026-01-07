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

"""Debcraft shlibdeps helper service."""

import pathlib
import subprocess
from collections.abc import Iterator
from typing import Any

from craft_cli import emit

from debcraft.elf import elf_utils

from .helper import HelperService

# Map soname and major to package name and version
_SonameMap = dict[tuple[str, str], tuple[str, str]]


class ShlibdepsService(HelperService):
    """Debcraft shlibdeps helper service.

    The shlibdeps helper will:
    - Scan prime dir for ELF files
    - Identify the DT_NEEDED entries from the dynamic session
    - Map sonames to package names and versions
    - Add packages to the list of dependencies

    To be implemented: add dependency version information and merge
    user-defined dependencies.
    """

    _packaged_shlibs: _SonameMap = {}
    _deb_info_shlibs: _SonameMap = {}

    def run(
        self,
        *,
        package_name: str,
        arch: str,
        prime_dir: pathlib.Path,
        state_dir: pathlib.Path,
        state_dir_map: dict[str, pathlib.Path],
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Find shared library dependencies."""
        primed_elf_files = elf_utils.get_elf_files(prime_dir)
        if not self._packaged_shlibs:
            self._packaged_shlibs = _read_packaged_shlibs(state_dir_map)
        if not self._deb_info_shlibs:
            self._deb_info_shlibs = _read_deb_info_shlibs(arch)

        lib_files: set[str] = set()
        undefined_symbols: set[str] = set()

        for elf_file in primed_elf_files:
            dependencies, symbols = _get_elf_dependencies(elf_file.path)
            lib_files.update(dependencies)
            undefined_symbols.update(symbols)

        pkg_deps: set[str] = set()

        for lib in lib_files:
            name, ver = None, None
            soname, major = lib.split(".so.")

            # Check if any dependency matches libs from this source
            shlib = self._packaged_shlibs.get((soname, major))
            if shlib:
                name, ver = shlib
                if name != package_name:
                    pkg_deps.add(f"{name} {ver}")
                continue

            # Check dependency in /var/lib/dpkg/info/*.shlibs files
            shlib = self._deb_info_shlibs.get((soname, major))
            if shlib:
                name, ver = shlib
                if name != package_name:
                    ver = _check_symbols(name, ver, undefined_symbols)
                    pkg_deps.add(f"{name} {ver}")

        pkg_list = sorted(pkg_deps)
        if pkg_list:
            dep_list = ", ".join(pkg_list)
            emit.progress(f"Package {package_name} dependencies: {dep_list}")

        output_file = state_dir / "shlibdeps"
        with output_file.open("w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in pkg_list)


def _read_packaged_shlibs(state_dir_map: dict[str, pathlib.Path]) -> _SonameMap:
    libmap: _SonameMap = {}
    for state_dir in state_dir_map.values():
        shlibs_files = state_dir.glob("*.shlibs")
        libmap |= _parse_shlibs_files(shlibs_files)
    return libmap


def _read_deb_info_shlibs(arch: str) -> _SonameMap:
    shlibs_files = pathlib.Path("/var/lib/dpkg/info").glob(f"*:{arch}.shlibs")
    return _parse_shlibs_files(shlibs_files)


def _parse_shlibs_files(shlibs_files: Iterator[pathlib.Path]) -> _SonameMap:
    """Obtain a soname to package map based on shlibs files."""
    libmap: _SonameMap = {}
    for shlibs_file in shlibs_files:
        with shlibs_file.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.split("#", 1)[0].strip()  # Remove comments
                if not line or line.startswith("udeb:"):
                    continue
                soname, maj, pkg, ver = _split_shlibs_line(line)
                libmap[(soname, maj)] = (pkg, ver)
    return libmap


def _get_elf_dependencies(binary: pathlib.Path) -> tuple[set[str], set[str]]:
    output = subprocess.run(
        ["readelf", "-d", binary], capture_output=True, text=True, check=True
    )
    sonames = set()
    for line in output.stdout.splitlines():
        if "Shared library:" in line:
            lib = line.split("[")[1].split("]")[0]
            sonames.add(lib)

    # Symbol extraction and verification here.
    symbols: set[str] = set()

    return sonames, symbols


def _split_shlibs_line(line: str) -> tuple[str, str, str, str]:
    soname, maj, pkg_ver = line.strip().split(maxsplit=2)
    pkg, *rest = pkg_ver.split(maxsplit=1)
    ver = rest[0] if rest else ""
    return soname, maj, pkg, ver


def _check_symbols(name: str, ver: str, undefined_symbols: set[str]) -> str:  # noqa: ARG001
    # Load .symbols file if exists and check minimum version.
    return ver
