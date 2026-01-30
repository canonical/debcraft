#  This file is part of debcraft.
#
#  Copyright 2025-2026 Canonical Ltd.
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

"""Debcraft base helper service."""

import pathlib
import tempfile
from typing import Any, cast

from craft_application import AppService
from craft_cli import emit
from craft_parts import StepInfo
from craft_platforms import BuildInfo
from typing_extensions import Self

from debcraft import models
from debcraft.helpers import InstallHelpers, PackagingHelpers
from debcraft.services.lifecycle import Lifecycle


class InstallHelpersRunner:
    """Run debcraft install helpers."""

    def __init__(
        self,
        project: models.Project,
        build_info: BuildInfo,
        step_info: StepInfo,
        lifecycle: Lifecycle,
    ) -> None:
        self._project = project
        self._build_info = build_info
        self._step_info = step_info
        self._lifecycle = lifecycle
        self._helpers = InstallHelpers()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def run(self, helper_name: str, **kwargs: Any) -> None:
        """Run the specified helper.

        :param helper_name: The name of the helper to run.
        :param kwargs: Optional arguments to the helper.
        """
        project = self._project
        if not project.packages:
            return

        helper = self._helpers.get_helper(helper_name)
        emit.debug(f"Running {helper_name} helper for all packages...")

        common_kwargs = {
            "step_info": self._step_info,
            "part_name": self._step_info.part_name,
            "project": project,
            "build_dir": self._step_info.part_build_dir,
            "install_dir": self._step_info.part_install_dir,
        }
        common_kwargs |= kwargs

        emit.debug(f"Running {helper_name} helper for part '{self._step_info.part_name}'")
        helper_run = getattr(helper, "run", None)
        if callable(helper_run):
            helper_run(**common_kwargs)
        else:
            raise RuntimeError(f"Helper '{helper_name}' is not runnable")  # noqa: TRY004


class PackagingHelpersRunner:
    """Run debcraft packaging helpers for all packages."""

    def __init__(
        self,
        project: models.Project,
        build_info: BuildInfo,
        lifecycle: Lifecycle,
    ) -> None:
        self._project = project
        self._build_info = build_info
        self._lifecycle = lifecycle
        self._temp_dir = tempfile.TemporaryDirectory()
        self._helpers = PackagingHelpers()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self._temp_dir.cleanup()

    def run(self, helper_name: str, **kwargs: Any) -> None:
        """Run the specified helper.

        :param helper_name: The name of the helper to run.
        :param kwargs: Optional arguments to the helper.
        """
        project = self._project
        if not project.packages:
            return

        helper = self._helpers.get_helper(helper_name)
        emit.debug(f"run {helper_name} helper for all packages...")

        for package_name, package in project.packages.items():
            prime_dir = self._lifecycle.get_prime_dir(package_name)
            arch = _get_architecture(package, self._build_info)
            if not arch:
                continue

            package_dir = pathlib.Path(self._temp_dir.name) / package_name
            control_dir = package_dir / "control"
            deb_dir = package_dir / "deb"
            state_dir = package_dir / "state"

            control_dir.mkdir(parents=True, exist_ok=True)
            deb_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)

            state_dir_map = {
                name: pathlib.Path(self._temp_dir.name) / name / "state"
                for name in project.packages
            }

            common_kwargs = {
                "prime_dir": prime_dir,
                "arch": arch,
                "control_dir": control_dir,
                "state_dir": state_dir,
                "deb_dir": deb_dir,
                "project": project,
                "package_name": package_name,
                "state_dir_map": state_dir_map,
            }
            common_kwargs |= kwargs

            emit.debug(f"run {helper_name} helper for package {package_name}")
            helper_run = getattr(helper, "run", None)
            if callable(helper_run):
                helper_run(**common_kwargs)
            else:
                raise RuntimeError(f"Helper '{helper_name}' is not runnable")  # noqa: TRY004


class HelperService(AppService):
    """Debcraft base helper Service."""

    def install_helpers(self, step_info: StepInfo) -> InstallHelpersRunner:
        """Obtain a runner for install helpers."""
        project = cast(models.Project, self._services.get("project").get())
        build_info = self._services.get("build_plan").plan()[0]
        lifecycle = cast(Lifecycle, self._services.lifecycle)
        return InstallHelpersRunner(project, build_info, step_info, lifecycle)

    def packaging_helpers(self) -> PackagingHelpersRunner:
        """Obtain a runner for packaging helpers."""
        project = cast(models.Project, self._services.get("project").get())
        build_info = self._services.get("build_plan").plan()[0]
        lifecycle = cast(Lifecycle, self._services.lifecycle)
        return PackagingHelpersRunner(project, build_info, lifecycle)


def _get_architecture(package: models.Package, build_info: BuildInfo) -> str | None:
    if package.architectures == "any":
        return build_info.build_for

    if package.architectures == "all":
        return "all"

    if build_info.build_for in package.architectures:
        return build_info.build_for

    return None
