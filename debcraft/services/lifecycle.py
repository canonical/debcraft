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
#
"""Debcraft Lifecycle Service."""

from pathlib import Path

from craft_application import LifecycleService
from craft_parts import ProjectInfo

from debcraft import errors


class Lifecycle(LifecycleService):
    """Debcraft specialization of the Lifecycle Service."""

    def get_prime_dir(self, package: str | None = None) -> Path:
        """Get the prime directory path for the default prime dir or a package.

        :param package: Name of the package to get the prime directory for.

        :returns: The default prime directory or a package's prime directory.

        :raises DebcraftError: If the package does not exist.
        """
        try:
            return self.prime_dirs[package]
        except KeyError as err:
            raise errors.DebcraftError(
                f"Could not get prime directory for package {package!r} "
                "because it does not exist."
            ) from err

    @property
    def prime_dirs(self) -> dict[str | None, Path]:
        """Return a mapping of package names to prime directories.

        'None' maps to the default prime directory.
        """
        return _get_prime_dirs_from_project(self._lcm.project_info)


def _get_prime_dirs_from_project(project_info: ProjectInfo) -> dict[str | None, Path]:
    """Get a mapping of package names to prime directories from a ProjectInfo.

    'None' maps to the default prime directory.

    :param project_info: The ProjectInfo to get the prime directory mapping from.
    """
    partition_prime_dirs = project_info.prime_dirs
    package_prime_dirs: dict[str | None, Path] = {None: project_info.prime_dir}

    # strip 'component/' prefix so that the package name is the key
    for partition, prime_dir in partition_prime_dirs.items():
        if partition and partition.startswith("package/"):
            package = partition.split("/", 1)[1]
            package_prime_dirs[package] = prime_dir

    return package_prime_dirs
