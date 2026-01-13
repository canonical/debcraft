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

import pathlib
import shutil
from typing import Any, cast

from craft_cli import emit

from debcraft import models
from debcraft.elf import elf_utils

from .helper import HelperService


class MakeshlibsService(HelperService):
    """Debcraft makeshlibs helper service.

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
        primed_elf_files = elf_utils.get_elf_files(prime_dir)
        primed_shlibs = [x for x in primed_elf_files if x.soname]

        if not primed_shlibs:
            emit.debug(f"no primed shlibs in package {package_name}")
            return

        # Write shlibs file
        with shlibs_file.open("w", encoding="utf-8") as f:
            for elf in primed_shlibs:
                name = elf.soname.split(".")
                if len(name) < 3 or name[1] != "so":  # noqa: PLR2004
                    emit.warning(f"cannot parse shlib soname: {elf.soname}")
                    continue

                emit.progress(f"ELF shared library: {elf.soname}")
                f.write(f"{name[0]} {name[2]} {package_name} (>= {version})\n")

        # Copy to helper state
        state_shlibs_file = state_dir / f"{package_name}:{arch}.shlibs"
        shutil.copy(shlibs_file, state_shlibs_file)
