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
"""Common fixtures and pytest configuration for integration tests."""

import pathlib

import craft_application
import debcraft
import pytest
from debcraft import services


@pytest.fixture
def real_services(in_project_path: pathlib.Path) -> craft_application.ServiceFactory:
    services.register_services()
    factory = craft_application.ServiceFactory(app=debcraft.METADATA)
    factory.update_kwargs("project", project_dir=in_project_path)
    return factory
