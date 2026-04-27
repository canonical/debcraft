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
from typing import TYPE_CHECKING, cast

from craft_application import LifecycleService
from craft_application.models import VersionStr
from craft_cli import emit
from craft_parts import StepInfo, callbacks
from craft_parts.steps import Step
from typing_extensions import override

from debcraft import errors, models

if TYPE_CHECKING:
    from debcraft.services.helper import HelperService


class Lifecycle(LifecycleService):
    """Debcraft specialization of the Lifecycle Service."""

    @override
    def setup(self) -> None:
        """Set up the lifecycle service."""
        callbacks.register_step(
            self._check_package_format,
            step_list=[Step.BUILD],
            hook_point=callbacks.HookPoint.PRE_ORGANIZE,
        )
        callbacks.register_step(
            self._run_install_helpers,
            step_list=[Step.BUILD],
            hook_point=callbacks.HookPoint.PRE_ORGANIZE,
        )

        self._manager_kwargs.update(
            is_native=None,
        )

        super().setup()

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
        project_info = self._lcm.project_info
        partition_prime_dirs = project_info.prime_dirs
        package_prime_dirs: dict[str | None, Path] = {None: project_info.prime_dir}

        # strip 'package/' prefix so that the package name is the key
        for partition, prime_dir in partition_prime_dirs.items():
            if partition and partition.startswith("package/"):
                package = partition.split("/", 1)[1]
                package_prime_dirs[package] = prime_dir

        return package_prime_dirs

    def _run_install_helpers(self, step_info: StepInfo) -> bool:
        project = cast(models.Project, self._services.get("project").get())
        if not project.parts:
            return True

        helper_service = cast("HelperService", self._services.helper)

        with helper_service.install_helpers(step_info) as helper:
            helper.run("installdocs")
            helper.run("installchangelogs")
            helper.run("strip")

        return True

    def _check_package_format(self, step_info: StepInfo) -> bool:
        if step_info.is_native is None:
            step_info.is_native = _is_native_package(  # type: ignore[attr-defined] # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[unresolved-attribute]
                build_dir=step_info.part_build_dir,
                version=step_info.project_vars.get("version").value,
            )

        return True


def _is_native_package(build_dir: Path, version: VersionStr | None) -> bool:
    """Determine whether a package is native or non-native.

    Look for the package format definition in the ``debian/source/format`` file
    and check if it's consistent with the presence of a revision in the package
    version number. Assume the package is non-native if the format can't be detected
    from the format file or version number.

    :param build_dir: The path to the package being built
    :param version: The package version number
    :return: Whether this package is a native Debian package.
    """
    format_file = build_dir / "debian" / "source" / "format"
    is_native = None

    # Check debian/source/format
    if format_file.exists():
        fmt = format_file.read_text().strip()
        emit.progress(f"Source format is {fmt}")
        if "native" in fmt:
            is_native = True
        elif "quilt" in fmt:
            is_native = False

    # Check project version
    if version is not None:
        emit.progress(f"Project version is {version}")
        version_is_native = "-" not in version

        if is_native is None:
            is_native = version_is_native
        elif is_native != version_is_native:
            raise errors.DebcraftError(
                "Mismatch in source format and version format.",
                details="Ensure the version is consistent with the declared package format.",
            )

    # Assume the package is not native if we can't detect the format.
    if is_native is None:
        is_native = False

    return is_native
