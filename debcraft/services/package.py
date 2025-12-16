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

"""Package service for debcraft."""

import pathlib
import tempfile
from typing import Any, cast

from craft_application import services
from craft_cli import emit
from craft_platforms import BuildInfo
from typing_extensions import Self, override

from debcraft import models
from debcraft.services.helper import HelperService
from debcraft.services.lifecycle import Lifecycle


class _HelperRunner:
    def __init__(
        self, project: models.Project, build_info: BuildInfo, lifecycle: Lifecycle
    ) -> None:
        self._project = project
        self._build_info = build_info
        self._lifecycle = lifecycle
        self._temp_dir = tempfile.TemporaryDirectory()

        emit.debug(f"create temporary directory {self._temp_dir.name}")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def run(
        self, helper_name: str, helper: HelperService, *args: Any, **kwargs: Any
    ) -> None:
        project = self._project
        build_info = self._build_info

        if not project.packages:
            return

        for package_name, package in project.packages.items():
            emit.debug(f"Run helper {helper_name} for package {package_name}")
            prime_dir = self._lifecycle.get_prime_dir(package_name)
            arch = _get_architecture(package, build_info)
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

            emit.debug(f"Run {helper_name} helper for package {package_name}")
            helper.run(*args, **common_kwargs)


class Package(services.PackageService):
    """Package service subclass for Debcraft."""

    @override
    def pack(self, prime_dir: pathlib.Path, dest: pathlib.Path) -> list[pathlib.Path]:
        """Create one or more packages as appropriate.

        :param dest: Directory into which to write the package(s).
        :returns: A list of paths to created packages.
        """
        project = cast(models.Project, self._services.get("project").get())
        build_info = self._services.get("build_plan").plan()[0]

        if not project.packages:
            return []

        lifecycle = cast(Lifecycle, self._services.lifecycle)
        debs: list[pathlib.Path] = []

        with _HelperRunner(project, build_info, lifecycle) as helper:
            # Run helpers
            helper.run(*self._get_helper("strip"))
            helper.run(*self._get_helper("md5sums"))
            helper.run(*self._get_helper("makeshlibs"))
            helper.run(*self._get_helper("shlibdeps"))
            helper.run(*self._get_helper("gencontrol"))
            helper.run(*self._get_helper("makedeb"), output_dir=dest, deb_list=debs)

        return debs

    def _get_helper(self, name: str) -> tuple[str, HelperService]:
        return (name, cast(HelperService, self._services.get(name)))

    @property
    def metadata(self) -> models.Metadata:
        """Generate the metadata.yaml model for the output file."""
        project = cast(models.Project, self._services.get("project").get())
        build_plan = self._services.get("build_plan").plan()[0]

        return models.Metadata(
            name=project.name,
            version=cast(str, project.version),
            architecture=build_plan.build_for,
        )


def _get_architecture(package: models.Package, build_info: BuildInfo) -> str | None:
    if package.architectures == "any":
        return build_info.build_for

    if package.architectures == "all":
        return "all"

    if build_info.build_for in package.architectures:
        return build_info.build_for

    return None
