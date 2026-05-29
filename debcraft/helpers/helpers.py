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

import os
import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from string import Template

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
        if pfile.is_symlink():
            dest.unlink(missing_ok=True)
            dest.symlink_to(pfile.readlink())
        else:
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
    template_mapping: dict[str, str] | None = None,
) -> None:
    """Install package-specific files from the debian directory.

    Read files named ``<package-name>.<name>`` from the ``debcraft/`` or
    ``debian/`` directories in the source package and add them to the
    control tarball of the corresponding package. A file named ``<name>``
    is also supported and is treated as applying to ``project.name``.
    If matching files exist in both directories for the same package,
    the file from ``debcraft/`` takes precedence over the one from ``debian/``.

    :param name: The name used as the file suffix.
    :param project: The project model.
    :param build_dir: The path to the sources being built.
    :param partition_dir: The path to the project partitions.
    :param install_dirs: The map to the part install directory in
        each partition.
    :param template_mapping: A mapping of strings to substitute into the file.
        If set to None, no substitutions are performed. If set to any dict,
        even an empty one, special template keys such as "ENV." will be filled
        in anyways.
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
        if pfile.is_symlink():
            dest.symlink_to(pfile.readlink())
        else:
            if template_mapping is None:
                shutil.copy(pfile, dest)
            else:
                contents = pfile.read_text()
                template_mapping |= _DebianTemplater.get_dynamic_values(contents)
                # Common substitution that can vary by the package being built
                template_mapping["PACKAGE"] = package
                contents = _DebianTemplater(contents).substitute(template_mapping)
                dest.write_text(contents)

            dest.chmod(0o644)

        emit.progress(f"Install {name} to package {package} control file")


def _build_file_map(
    name: str, project_name: str, debian_dirs: list[Path]
) -> dict[str, Path]:
    file_map: dict[str, Path] = {}

    for debian_dir in debian_dirs:
        default_file = debian_dir / name
        if default_file.is_file() or default_file.is_symlink():
            file_map[project_name] = default_file

        package_files = debian_dir.glob(f"*.{name}")
        for pfile in package_files:
            if pfile.is_file() or pfile.is_symlink():
                package_name = pfile.name.removesuffix(f".{name}")
                file_map[package_name] = pfile

    return file_map


_VALID_CONFIG_TEMPLATE_REGEX = "[A-Za-z0-9_.+]+"


class _DebianTemplater(Template):
    """A templating structure to fill in token templates in debian config files."""

    # https://docs.python.org/3/library/string.html#template-strings-strings
    #
    # \#                                                     The first character to look for to begin replacement
    #   (?:                                                  Non-capturing group that must come after the #
    #     (?<escaped>\#)                              |      What it looks like when the user wants to escape the
    #                                                 |      template sequence. In this case, ## becomes a literal
    #                                                 |      '#' in the final output.
    #     (?P<named>{_VALID_CONFIG_TEMPLATE_REGEX})   |      Match a valid key that would go between #'s.
    #                                              \# |      Enforce a closing '#' for the template string.
    #     (?P<braced>(?!))                            |      Unused, never matches
    #     (?P<invalid>{_VALID_CONFIG_TEMPLATE_REGEX}(?!\#))  What an invalid match looks like -- in this case, an
    #                                                        identifier that isn't terminated by a '#'.
    #   )                                                    End
    pattern = rf"""
        \#(?:
            (?P<escaped>\#)                             |
            (?P<named>{_VALID_CONFIG_TEMPLATE_REGEX})\# |
            (?P<braced>(?!))                            |
            (?P<invalid>{_VALID_CONFIG_TEMPLATE_REGEX}(?!\#))
        )
    """
    delimiter = "#"

    @classmethod
    def get_dynamic_values(cls, contents: str) -> dict[str, str]:
        mapping = {}

        for needle in re.finditer(cls.pattern, contents):
            key = needle.group("named")
            if not key:
                continue

            # Populate "ENV." values
            if key.startswith("ENV."):
                _, name = key.split(".", maxsplit=1)
                # Default to an empty string to stay bashy
                mapping[key] = os.getenv(name, "")

        return mapping
