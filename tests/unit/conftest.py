#  This file is part of debcraft.
#
#  Copyright 2023-2025 Canonical Ltd.
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
"""Configuration for debcraft unit tests."""

import pathlib
from typing import Any, cast

import debcraft
import debcraft.services.package
import debcraft.services.project
import pytest
from debcraft import models, services
from typing_extensions import override


@pytest.fixture
def extra_project_params():
    """Configuration fixture for the Project used by the default services."""
    return {}


@pytest.fixture
def default_project_raw(
    extra_project_params: dict[str, Any], host_architecture: str
) -> dict[str, Any]:
    parts = extra_project_params.pop("parts", {})

    return {
        "name": "fake-project",
        "version": "1.0",
        "base": "ubuntu@24.04",
        "platforms": {host_architecture: None},
        "parts": parts,
        "maintainer": "Mike Maintainer <someone@example.com>",
    } | extra_project_params


@pytest.fixture
def default_project(default_project_raw: dict[str, Any]) -> models.Project:
    return models.Project.model_validate(default_project_raw)


@pytest.fixture
def fake_project_service_class(
    default_project_raw: dict[str, Any],
    default_project: models.Project,
) -> type[debcraft.services.project.Project]:
    class FakeProjectService(debcraft.services.project.Project):
        @override
        def _load_raw_project(self) -> dict[str, Any]:  # type: ignore[reportIncompatibleMethodOverride]
            return default_project_raw

        @override
        def resolve_project_file_path(self):
            return (self._project_dir / f"{self._app.name}.yaml").resolve()

        def set(self, value: models.Project) -> None:
            """Set the project model. Only for use during testing!"""
            self._project_model = value
            self._platform = next(iter(value.platforms))
            self._build_for = value.platforms[self._platform].build_for[0]  # type: ignore[reportOptionalSubscript]

    return FakeProjectService


@pytest.fixture
def default_factory(
    default_project,
    fake_project_service_class,
    project_path: pathlib.Path,
) -> services.ServiceFactory:
    services.ServiceFactory.register(
        "package", "Package", module="debcraft.services.package"
    )
    services.ServiceFactory.register("project", fake_project_service_class)
    service_factory = services.ServiceFactory(app=debcraft.METADATA)
    service_factory.update_kwargs("project", project_dir=project_path)
    return service_factory


@pytest.fixture
def package_service(default_factory) -> debcraft.services.package.Package:
    return cast(debcraft.services.package.Package, default_factory.package)


@pytest.fixture
def build_plan_service(default_factory) -> services.BuildPlan:
    return cast(services.BuildPlan, default_factory.get("build_plan"))


@pytest.fixture
def project_service(default_factory) -> debcraft.services.project.Project:
    return cast(debcraft.services.project.Project, default_factory.get("project"))
