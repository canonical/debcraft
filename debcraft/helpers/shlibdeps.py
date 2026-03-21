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
from collections.abc import Iterator
from typing import Any, Self

from craft_cli import emit

from debcraft import errors
from debcraft.elf import ElfLibrary, get_elf_files

from .helpers import Helper

_DPKG_INFO_DIR = pathlib.Path("/var/lib/dpkg/info")


class _SonameMap(dict[tuple[str, str], str]):
    @classmethod
    def from_packaged_shlibs(cls, state_dir_map: dict[str, pathlib.Path]) -> Self:
        libmap = cls()
        for state_dir in state_dir_map.values():
            shlibs_files = state_dir.glob("*.shlibs")
            libmap |= cls._parse_shlibs_files(shlibs_files)
        return libmap

    @classmethod
    def from_deb_info_shlibs(cls, arch: str) -> Self:
        shlibs_files = _DPKG_INFO_DIR.glob(f"*:{arch}.shlibs")
        return cls._parse_shlibs_files(shlibs_files)

    @classmethod
    def _parse_shlibs_files(cls, shlibs_files: Iterator[pathlib.Path]) -> Self:
        """Obtain a soname to package map based on shlibs files."""
        libmap = cls()
        for shlibs_file in shlibs_files:
            with shlibs_file.open("r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.split("#", 1)[0].strip()  # Remove comments
                    if not line or line.startswith("udeb:"):
                        continue
                    soname, maj, pkgdeps = cls._split_shlibs_line(line)
                    libmap[(soname, maj)] = pkgdeps
        return libmap

    @staticmethod
    def _split_shlibs_line(line: str) -> tuple[str, str, str]:
        # Example line from /var/lib/dpkg/info/libbinutils:amd64.shlibs:
        # libopcodes 2.42-system libbinutils (>= 2.42), libbinutils (<< 2.42.1)
        parts = line.strip().split(maxsplit=2)
        if len(parts) < 3:  # noqa: PLR2004
            raise errors.DebcraftError(f"malformed shlibs entry: {line.strip()}")

        soname, maj, pkgdeps = parts
        return soname, maj, pkgdeps


class _SymbolMap(dict[str, dict[str, str]]):
    @classmethod
    def from_packaged_symbols(cls, state_dir_map: dict[str, pathlib.Path]) -> Self:
        symmap = cls()
        for state_dir in state_dir_map.values():
            symbols_files = state_dir.glob("*.symbols")
            symmap |= cls._parse_symbols_files(symbols_files)
        return symmap

    @classmethod
    def from_deb_info_symbols(cls, arch: str) -> Self:
        symbols_files = _DPKG_INFO_DIR.glob(f"*:{arch}.symbols")
        return cls._parse_symbols_files(symbols_files)

    @classmethod
    def _parse_symbols_files(cls, symbols_files: Iterator[pathlib.Path]) -> Self:
        """Obtain library to symbol maps based on symbols files."""
        symmap = cls()
        for symbols_file in symbols_files:
            pkgmap: dict[str, str] | None = None
            with symbols_file.open("r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.split("#", 1)[0].strip()  # Remove comments

                    if line.startswith("SONAME "):  # Header with package name
                        parts = line.split()
                        if len(parts) >= 2:  # noqa: PLR2004
                            pkgname = parts[1]
                            pkgmap = symmap[pkgname] = {}

                    if not line or not line.startswith(" "):
                        continue

                    symbol, version = cls._split_symbols_line(line)
                    if pkgmap is None:
                        continue

                    pkgmap[symbol] = version

        return symmap

    @staticmethod
    def _split_symbols_line(line: str) -> tuple[str, str]:
        parts = line.strip().split(maxsplit=1)
        if len(parts) < 2:  # noqa: PLR2004
            raise errors.DebcraftError(f"malformed symbols entry: {line.strip()}")

        symbol, version = parts
        return symbol, version


class Shlibdeps(Helper):
    """Debcraft shlibdeps helper.

    The shlibdeps helper will:
    - Scan prime dir for ELF files
    - Identify the DT_NEEDED entries from the dynamic session
    - Map sonames to package names and versions
    - Map unresolved ELF symbols to package version
    - Add packages to the list of dependencies based on symbols or library names

    To be implemented: add dependency version information and merge
    user-defined dependencies.
    """

    _packaged_symbols: _SymbolMap | None = None
    _deb_info_symbols: _SymbolMap | None = None
    _packaged_shlibs: _SonameMap | None = None
    _deb_info_shlibs: _SonameMap | None = None

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
        primed_elf_files = get_elf_files(prime_dir)

        if not self._packaged_symbols:
            self._packaged_symbols = _SymbolMap.from_packaged_symbols(state_dir_map)
        if not self._deb_info_symbols:
            self._deb_info_symbols = _SymbolMap.from_deb_info_symbols(arch)
        if not self._packaged_shlibs:
            self._packaged_shlibs = _SonameMap.from_packaged_shlibs(state_dir_map)
        if not self._deb_info_shlibs:
            self._deb_info_shlibs = _SonameMap.from_deb_info_shlibs(arch)

        lib_files: set[ElfLibrary] = set()
        undefined_symbols: set[str] = set()

        # Obtain the list of ELF file dependencies
        for elf_file in primed_elf_files:
            lib_files.update(elf_file.needed)
            undefined_symbols.update(elf_file.symbols)

        pkg_deps: set[str] = set()

        for lib in lib_files:
            # Check if any dependency matches libs from this source
            raw_deps = self._packaged_shlibs.get((lib.libname, lib.ver))
            if raw_deps and not _package_in_deps(package_name, raw_deps):
                pkg_deps.add(raw_deps)
                continue

            # Check dependency in /var/lib/dpkg/info/*.shlibs files
            raw_deps = self._deb_info_shlibs.get((lib.libname, lib.ver))
            if raw_deps and not _package_in_deps(package_name, raw_deps):
                pkg_deps.add(raw_deps)

        pkg_list = sorted(pkg_deps)
        if pkg_list:
            dep_list = ", ".join(pkg_list)
            emit.progress(f"{package_name} dependencies: {dep_list}")

        output_file = state_dir / "shlibdeps"
        with output_file.open("w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in pkg_list)


def _package_in_deps(package_name: str, raw_deps: str) -> bool:
    if not raw_deps:
        return False

    # Handle "and" dependency blocks
    for and_block in raw_deps.split(","):
        # Handle "or" dependency blocks
        for or_block in and_block.split("|"):
            name = or_block.strip().split()[0]
            if package_name == name:
                return True

    return False
