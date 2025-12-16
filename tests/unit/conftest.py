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

import craft_application
import debcraft
import debcraft.services.md5sums
import debcraft.services.package
import debcraft.services.project
import pytest
from debcraft import models, services
from debcraft.services import gencontrol, lifecycle, makedeb, makeshlibs, md5sums, strip
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
        "summary": "A package",
        "description": "Really a package",
        "platforms": {host_architecture: None},
        "parts": parts,
        "maintainer": "Mike Maintainer <someone@example.com>",
        "section": "libs",
        "packages": {"package-1": {"version": "2.0"}},
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
def fake_lifecycle_service_class(tmp_path, host_architecture):
    class FakeLifecycleService(lifecycle.Lifecycle):
        def __init__(
            self,
            app: craft_application.AppMetadata,
            services: services.ServiceFactory,
            **lifecycle_kwargs: Any,
        ):
            super().__init__(
                app,
                services,
                work_dir=tmp_path / "work",
                cache_dir=tmp_path / "cache",
                platform=None,
                build_for=host_architecture,
                **lifecycle_kwargs,
            )

    return FakeLifecycleService


@pytest.fixture
def fake_md5sums_service_class(tmp_path, host_architecture):
    class FakeMd5sumsService(md5sums.Md5sumsService):
        def __init__(
            self,
            app: craft_application.AppMetadata,
            services: services.ServiceFactory,
        ):
            super().__init__(app, services)

    return FakeMd5sumsService


@pytest.fixture
def fake_strip_service_class(tmp_path, host_architecture):
    class FakeStripService(strip.StripService):
        def __init__(
            self,
            app: craft_application.AppMetadata,
            services: services.ServiceFactory,
        ):
            super().__init__(app, services)

    return FakeStripService


@pytest.fixture
def fake_makeshlibs_service_class(tmp_path, host_architecture):
    class FakeMakeshlibsService(makeshlibs.MakeshlibsService):
        def __init__(
            self,
            app: craft_application.AppMetadata,
            services: services.ServiceFactory,
        ):
            super().__init__(app, services)

    return FakeMakeshlibsService


@pytest.fixture
def fake_gencontrol_service_class(tmp_path, host_architecture):
    class FakeGencontrolService(gencontrol.GencontrolService):
        def __init__(
            self,
            app: craft_application.AppMetadata,
            services: services.ServiceFactory,
        ):
            super().__init__(app, services)

    return FakeGencontrolService


@pytest.fixture
def fake_makedeb_service_class(tmp_path, host_architecture):
    class FakeMakedebService(makedeb.MakedebService):
        def __init__(
            self,
            app: craft_application.AppMetadata,
            services: services.ServiceFactory,
        ):
            super().__init__(app, services)

    return FakeMakedebService


@pytest.fixture
def default_factory(
    default_project,
    fake_project_service_class,
    fake_lifecycle_service_class,
    fake_strip_service_class,
    fake_md5sums_service_class,
    fake_makeshlibs_service_class,
    fake_gencontrol_service_class,
    fake_makedeb_service_class,
    project_path: pathlib.Path,
) -> services.ServiceFactory:
    services.ServiceFactory.register(
        "package", "Package", module="debcraft.services.package"
    )
    services.ServiceFactory.register("project", fake_project_service_class)
    services.ServiceFactory.register("lifecycle", fake_lifecycle_service_class)
    services.ServiceFactory.register("strip", fake_strip_service_class)
    services.ServiceFactory.register("md5sums", fake_md5sums_service_class)
    services.ServiceFactory.register("makeshlibs", fake_makeshlibs_service_class)
    services.ServiceFactory.register("gencontrol", fake_gencontrol_service_class)
    services.ServiceFactory.register("makedeb", fake_makedeb_service_class)
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


@pytest.fixture
def md5sums_service(default_factory) -> debcraft.services.md5sums.Md5sumsService:
    return cast(debcraft.services.md5sums.Md5sumsService, default_factory.md5sums)
