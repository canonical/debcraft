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
from typing import Any

from craft_cli import emit

from debcraft import errors, util
from debcraft.elf import ElfLibrary, get_elf_files

from .helpers import Helper

_DPKG_INFO_DIR = pathlib.Path("/var/lib/dpkg/info")


class _LibraryMap:
    """Library to package name mapping.

    To determine the package that contains a given shared library, we
    read the soname to library path information from the dynamic linker
    and check the list of files belonging to each package on the system.
    """

    def __init__(self, arch: str) -> None:
        self.soname_to_package: dict[str, str] = {}
        soname_to_path = self._get_soname_to_path()
        path_to_package = self._get_path_to_package(arch)
        for soname, path in soname_to_path.items():
            list_path = path_to_package.get(path)
            if not list_path and path.startswith("/lib"):
                list_path = path_to_package.get("/usr" + path)  # usrmerge
            if list_path:
                self.soname_to_package[soname] = list_path
        emit.debug(f"shlibdeps: {len(self.soname_to_package)} library map entries")

    @staticmethod
    def _get_path_to_package(arch: str) -> dict[str, str]:
        index: dict[str, str] = {}
        list_files = _DPKG_INFO_DIR.glob(f"*:{arch}.list")

        for list_file in list_files:
            with list_file.open("r", encoding="utf-8") as f:
                pkg_name = list_file.stem.split(":", 1)[0]
                for raw_line in f:
                    line = raw_line.strip()
                    if ".so." in line:
                        index[line] = pkg_name

        return index

    @staticmethod
    def _get_soname_to_path() -> dict[str, str]:
        """Run ldconfig -p to obtain the current linker cache."""
        try:
            res = subprocess.run(
                ["ldconfig", "-p"], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as err:
            raise errors.DebcraftError(
                f"ldconfig failed with exit code {err.returncode}"
            )
        except FileNotFoundError:
            raise errors.DebcraftError("ldconfig not found on this system")

        mapping: dict[str, str] = {}

        for line in res.stdout.splitlines():
            parts = line.strip().split(" => ")
            if len(parts) > 1:
                soname, path = parts[0].split(" ", 1)[0], parts[1]
                mapping[soname] = path

        return mapping


class _SonameMap(dict[str, str]):
    """Mapping of soname to dependency."""

    def __init__(self, libmap: _LibraryMap) -> None:
        self._libmap = libmap

    def load_packaged_shlibs(self, state_dir_map: dict[str, pathlib.Path]) -> None:
        for state_dir in state_dir_map.values():
            shlibs_files = state_dir.glob("*.shlibs")
            for shlibs_file in shlibs_files:
                self._load_shlibs_file(shlibs_file)

    def load_deb_info_shlibs(self, soname: str, arch: str) -> None:
        if not self._libmap.soname_to_package:
            return

        if soname in self:
            return

        package = self._libmap.soname_to_package.get(soname)
        emit.debug(f"shlibdeps: load shlibs for {soname} (package: {package})")
        if package:
            shlibs_file = _DPKG_INFO_DIR / f"{package}:{arch}.shlibs"
            if shlibs_file.exists():
                self._load_shlibs_file(shlibs_file)

    def _load_shlibs_file(self, path: pathlib.Path) -> None:
        emit.debug(f"shlibdeps: load shlibs file: {path!s}")
        with path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.split("#", 1)[0].strip()  # Remove comments
                if not line or line.startswith("udeb:"):
                    continue
                libname, maj, pkgdeps = self._split_shlibs_line(line)
                self[f"{libname}.so.{maj}"] = pkgdeps

    @staticmethod
    def _split_shlibs_line(line: str) -> tuple[str, str, str]:
        # Example line from /var/lib/dpkg/info/libbinutils:amd64.shlibs:
        # libopcodes 2.42-system libbinutils (>= 2.42), libbinutils (<< 2.42.1)
        parts = line.strip().split(maxsplit=2)
        if len(parts) < 3:  # noqa: PLR2004
            raise errors.DebcraftError(f"malformed shlibs entry: {line.strip()}")

        libname, maj, pkgdeps = parts
        return libname, maj, pkgdeps


class _SymbolMap(dict[tuple[str, str], tuple[str, str]]):
    """Mapping of (soname, symbol) to (package, version)."""

    def __init__(self, libmap: _LibraryMap) -> None:
        self._libmap = libmap

    def load_packaged_symbols(self, state_dir_map: dict[str, pathlib.Path]) -> None:
        for state_dir in state_dir_map.values():
            symbols_files = state_dir.glob("*.symbols")
            for symbols_file in symbols_files:
                self._load_symbols_file(symbols_file)

    def load_deb_info_symbols(self, soname: str, arch: str) -> None:
        if not self._libmap.soname_to_package:
            return

        package = self._libmap.soname_to_package.get(soname)
        emit.debug(f"shlibdeps: load symbols for {soname} (package: {package})")
        if package:
            symbols_file = _DPKG_INFO_DIR / f"{package}:{arch}.symbols"
            if symbols_file.exists():
                self._load_symbols_file(symbols_file)

    def _load_symbols_file(self, path: pathlib.Path) -> None:
        """Obtain library symbol maps based on symbols files."""
        soname = ""
        pkgname = ""

        emit.debug(f"shlibdeps: load symbols file: {path!s}")
        with path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.split("#", 1)[0].rstrip()  # Remove comments
                if not line:
                    continue

                # Read the soname and package line. Alternative library names
                # support is not implemented yet.
                if not line.startswith((" ", "*", "|")):
                    parts = line.split()
                    if len(parts) >= 2:  # noqa: PLR2004
                        soname = parts[0]
                        pkgname = parts[1]
                        continue

                if not line.startswith(" "):
                    continue

                if not soname or not pkgname:
                    continue

                symbol, version = self._split_symbols_line(line)
                self[(soname, symbol)] = (pkgname, version)
                emit.debug(
                    f"shlibdeps: {path.name}: ({soname}, {symbol}) -> ({pkgname}, {version})"
                )

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
    - Map unresolved ELF symbols to package name and version
    - Map sonames to package name and versions
    - Add packages to the list of dependencies based on symbols or library names
    """

    def __init__(self) -> None:
        self._deb_info_symbols: _SymbolMap | None = None
        self._packaged_shlibs: _SonameMap | None = None
        self._deb_info_shlibs: _SonameMap | None = None
        self._libmap: _LibraryMap | None = None

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

        # Needed libraries and undefined symbols in primed ELF files.
        needed_libs: list[ElfLibrary] = []
        undefined_symbols: set[str] = set()

        # Obtain the list of ELF file dependencies
        for elf_file in primed_elf_files:
            needed_libs += elf_file.needed
            undefined_symbols.update(elf_file.read_symbols())

        # Deduplicate list of needed libraries.
        unique_needed_libs = list(dict.fromkeys(needed_libs))

        self._setup_shlibdeps(arch, state_dir_map)

        # Mapping of package name to a set of symbol versions, used to
        # determine the minimum package version containing all symbols.
        pkg_versions: dict[str, set[str]] = {}
        pkg_deps: set[str] = set()

        for lib in unique_needed_libs:
            self._deb_info_shlibs.load_deb_info_shlibs(lib.soname, arch)  # type: ignore[union-attr] # pyright: ignore[reportOptionalMemberAccess]
            self._deb_info_symbols.load_deb_info_symbols(lib.soname, arch)  # type: ignore[union-attr] # pyright: ignore[reportOptionalMemberAccess]

            # Check symbols
            emit.debug(f"shlibdeps: check library: {lib}")

            if self._add_deb_info_symbol_deps(lib, undefined_symbols, pkg_versions):
                continue

            if self._add_packaged_shlibs_deps(package_name, lib, pkg_deps):
                continue

            self._add_deb_info_shlibs_deps(package_name, lib, pkg_deps)

        for name, versions in pkg_versions.items():
            max_ver = util.get_max_debian_version(versions)
            if max_ver:
                pkg_deps.add(f"{name} (>= {max_ver})")
                emit.debug(f"shlibdeps: {name} version: {max_ver}")

        pkg_list = sorted(pkg_deps)
        if pkg_list:
            dep_list = ", ".join(pkg_list)
            emit.progress(f"Found {package_name} dependencies: {dep_list}")

        output_file = state_dir / "shlibdeps"
        with output_file.open("w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in pkg_list)

    def _add_deb_info_symbol_deps(
        self,
        lib: ElfLibrary,
        undefined_symbols: set[str],
        pkg_versions: dict[str, set[str]],
    ) -> bool:
        found_symbols: set[str] = set()

        for symbol in undefined_symbols:
            pkg, ver = self._deb_info_symbols.get((lib.soname, symbol), ("", ""))  # type: ignore[union-attr] # pyright: ignore[reportOptionalMemberAccess]
            if pkg and ver:
                if pkg not in pkg_versions:
                    pkg_versions[pkg] = set()
                pkg_versions[pkg].add(ver)
                found_symbols.add(symbol)
                emit.debug(
                    f"shlibdeps: found symbol ({lib.soname}, {symbol}) -> ({pkg}, {ver})"
                )

        # Stop looking for symbols we already found
        undefined_symbols -= found_symbols

        return bool(found_symbols)

    def _add_packaged_shlibs_deps(
        self, package_name: str, lib: ElfLibrary, pkg_deps: set[str]
    ) -> bool:
        """Check if any dependency matches libs from this source."""
        if self._packaged_shlibs is None:
            return False

        raw_deps = self._packaged_shlibs.get(lib.soname)  # pyright: ignore[reportOptionalMemberAccess]
        emit.debug(f"shlibdeps: check for {lib.soname} in sibling shlibs: {raw_deps}")

        if raw_deps and not _package_in_deps(package_name, raw_deps):
            pkg_deps.add(raw_deps)

        return bool(raw_deps)

    def _add_deb_info_shlibs_deps(
        self, package_name: str, lib: ElfLibrary, pkg_deps: set[str]
    ) -> None:
        """Check dependency in /var/lib/dpkg/info/*.shlibs files."""
        raw_deps = self._deb_info_shlibs.get(lib.soname)  # type: ignore[union-attr]
        emit.debug(f"shlibdeps: check for {lib.soname} in system shlibs: {raw_deps}")
        if raw_deps and not _package_in_deps(package_name, raw_deps):
            pkg_deps.add(raw_deps)

    def _setup_shlibdeps(
        self, arch: str, state_dir_map: dict[str, pathlib.Path]
    ) -> None:
        if self._libmap is None:
            self._libmap = _LibraryMap(arch)

        if self._deb_info_symbols is None:
            self._deb_info_symbols = _SymbolMap(self._libmap)

        if self._packaged_shlibs is None:
            self._packaged_shlibs = _SonameMap(self._libmap)
            self._packaged_shlibs.load_packaged_shlibs(state_dir_map)

        if self._deb_info_shlibs is None:
            self._deb_info_shlibs = _SonameMap(self._libmap)


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
