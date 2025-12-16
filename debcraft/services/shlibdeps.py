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

"""Debcraft shlibdeps helper service."""

import pathlib
import subprocess
from typing import Any

from craft_cli import emit

from debcraft.elf import SonameCache, elf_utils

from .helper import HelperService


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

    _soname_cache = SonameCache()

    def run(
        self,
        *,
        package_name: str,
        prime_dir: pathlib.Path,
        state_dir: pathlib.Path,
        state_dir_map: dict[str, pathlib.Path],
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Find shared library dependencies."""
        primed_elf_files = elf_utils.get_elf_files(prime_dir)
        packaged_shlibs = _read_packaged_shlibs(state_dir_map)

        lib_files: set[pathlib.Path] = set()
        for elf_file in primed_elf_files:
            arch_triplet = elf_utils.get_arch_triplet()

            dependencies = elf_file.load_dependencies(
                root_path=prime_dir,
                arch_triplet=arch_triplet,
                soname_cache=self._soname_cache,
            )

            lib_files.update(dependencies)

        pkg_deps: set[str] = set()

        for lib in lib_files:
            shlibs = packaged_shlibs.get(str(lib))
            if not shlibs:
                shlibs = packaged_shlibs.get(str(_usrmerged(lib)))

            name, ver = None, None
            if shlibs:
                name, ver = shlibs

            if name:
                if name != package_name:
                    pkg_deps.add(f"{name} (= {ver})")
            else:
                name = _find_deb_package(lib)

                if not name and lib.is_relative_to("/lib"):
                    name = _find_deb_package(_usrmerged(lib))

                if name:
                    pkg_deps.add(name)

        if pkg_deps:
            dep_list = ", ".join(pkg_deps)
            emit.progress(f"Package {package_name} dependencies: {dep_list}")

        output_file = state_dir / "shlibdeps"
        with output_file.open("w", encoding="utf-8") as f:
            f.writelines(line + "\n" for line in pkg_deps)


def _read_packaged_shlibs(
    state_dir_map: dict[str, pathlib.Path],
) -> dict[str, tuple[str, str]]:
    libmap: dict[str, tuple[str, str]] = {}
    for state_dir in state_dir_map.values():
        shlibs_file = state_dir / "makeshlibs"
        if not shlibs_file.exists():
            continue

        with shlibs_file.open("r", encoding="utf-8") as f:
            for line in f:
                lib, pkg, ver = line.split(maxsplit=2)
                libmap[lib] = (pkg, ver)

    return libmap


def _find_deb_package(library_path: pathlib.Path) -> str | None:
    """Find the deb package that provides a library.

    :param library_name: The filename of the library to find.

    :returns: the corresponding deb package name, or None if the library
    is not provided by any system package.
    """
    try:
        output = subprocess.run(
            ["dpkg", "-S", library_path.as_posix()],
            check=True,
            stdout=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        # If the specified file doesn't belong to any package, the
        # call will trigger an exception.
        return None
    except FileNotFoundError:
        # In case that dpkg isn't available
        return None

    name = output.stdout.decode("UTF-8").split(":", maxsplit=1)[0]
    emit.debug(f"find deb package: {library_path} -> {name}")

    return name


def _usrmerged(lib: pathlib.Path) -> pathlib.Path:
    return pathlib.Path("/usr") / lib.relative_to(lib.anchor)
