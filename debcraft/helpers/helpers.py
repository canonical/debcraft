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

"""Debcraft helpers base."""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from craft_cli import emit

from debcraft import models


class Helper:
    """Debcraft helper base class."""


class HelperGroup(ABC):
    """A collection of Debcraft helpers."""

    def __init__(self) -> None:
        self._helper_class: dict[str, type[Helper]] = {}
        self._helper: dict[str, Helper | None] = {}
        self._register()

    @abstractmethod
    def _register(self) -> None:
        """Register all helpers in this helper group."""

    def _register_helper(self, name: str, helper_class: type[Helper]) -> None:
        self._helper_class[name] = helper_class
        self._helper[name] = None

    def get_helper(self, name: str) -> Helper:
        """Obtain the instance of the named helper.

        :param name: The name of the helper.
        :returns: The instance of the named helper.
        """
        if name not in self._helper_class:
            raise ValueError(f"helper '{name}' is not registered.")

        helper = self._helper.get(name)
        if not helper:
            helper = self._helper_class[name]()
            self._helper[name] = helper

        return helper


def install_package_data(
    *,
    name: str,
    project: models.Project,
    dest_dir: Path,
    build_dir: Path,
    install_dirs: dict[str, Path],
) -> None:
    """Install package-specific files from the packaging directories.

    Read files named ``<package-name>.<name>`` from the ``debian/`` or
    ``debcraft/`` directories in the source package and copy them to the
    destination path in the corresponding package, with the suffix
    removed. A default file named ``<name>`` is also supported and is
    treated as applying to ``project.name``. If matching files exist in
    both directories for the same package, the file from ``debcraft/``
    takes precedence over the one from ``debian/``.

    :param name: The name used as the file suffix.
    :param project: The project model.
    :param dest_dir: The destination path in the binary package.
    :param build_dir: The path to the sources being built.
    :param install_dirs: The map to the part install directory in
        each partition.
    """
    file_map = _build_file_map(
        name,
        project_name=project.name,
        debian_dirs=[build_dir / "debian", build_dir / "debcraft"],
    )

    for partition, install_dir in install_dirs.items():
        if partition in ("default", "build"):
            continue

        package = partition.removeprefix("package/")
        pfile = file_map.get(package)
        if not pfile:
            continue

        file_path = Path(dest_dir) / package
        dest = install_dir / file_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Add this to a state file to be able to properly clean installed files.
        shutil.copy(pfile, dest)
        dest.chmod(0o644)
        emit.progress(f"Install {name} file: {file_path}")


def install_package_control(
    *,
    name: str,
    project: models.Project,
    build_dir: Path,
    partition_dir: Path,
    install_dirs: dict[str, Path],
) -> None:
    """Install package-specific files from the debian directory.

    Read files named ``<package-name>.<name>`` from the ``debcraft/`` or
    ``debian/`` directories in the source package and add them to the
    control tarball of the corresponding package.

    :param name: The name used as the file suffix.
    :param project: The project model.
    :param build_dir: The path to the sources being built.
    :param partition_dir: The path to the project partitions.
    :param install_dirs: The map to the part install directory in
        each partition.
    """
    file_map = _build_file_map(
        name,
        project_name=project.name,
        debian_dirs=[build_dir / "debian", build_dir / "debcraft"],
    )

    for partition in install_dirs:
        if partition in ("default", "build"):
            continue

        package = partition.removeprefix("package/")
        pfile = file_map.get(package)
        if not pfile:
            continue

        dest = partition_dir / "package" / package / "debcraft_control" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Add this to a state file to be able to properly clean installed files.
        shutil.copy(pfile, dest)
        dest.chmod(0o644)
        emit.progress(f"Install {name} to package {package} control file")


def _build_file_map(
    name: str, project_name: str, debian_dirs: list[Path]
) -> dict[str, Path]:
    file_map: dict[str, Path] = {}

    for debian_dir in debian_dirs:
        default_file = debian_dir / name
        if default_file.is_file():
            file_map[project_name] = default_file

        package_files = debian_dir.glob(f"*.{name}")
        for pfile in package_files:
            if pfile.is_file():
                package_name = pfile.name.removesuffix(f".{name}")
                file_map[package_name] = pfile

    return file_map
