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
"""Tests for loading full debcraft YAML files."""

import pathlib
import re
import shutil

import craft_application
import pytest
from craft_application.errors import CraftValidationError

VALID_PROJECTS_DIR = pathlib.Path(__file__).parent / "valid-projects"
INVALID_PROJECTS_DIR = pathlib.Path(__file__).parent / "invalid-projects"


@pytest.mark.parametrize(
    "project_dir", [pytest.param(d, id=d.name) for d in VALID_PROJECTS_DIR.iterdir()]
)
def test_load_project(
    real_services: craft_application.ServiceFactory,
    project_dir: pathlib.Path,
    in_project_path,
):
    shutil.copytree(project_dir, in_project_path, dirs_exist_ok=True)
    project_service = real_services.get("project")
    project_service.configure(platform=None, build_for=None)
    project_service.get()


@pytest.mark.parametrize(
    "project_dir", [pytest.param(d, id=d.name) for d in INVALID_PROJECTS_DIR.iterdir()]
)
def test_load_invalid_project(
    real_services: craft_application.ServiceFactory,
    project_dir: pathlib.Path,
    in_project_path,
):
    shutil.copytree(project_dir, in_project_path, dirs_exist_ok=True)
    error_message = re.escape((project_dir / "error-message.txt").read_text().rstrip())
    project_service = real_services.get("project")
    project_service.configure(platform=None, build_for=None)
    with pytest.raises(CraftValidationError, match=error_message):
        project_service.get()
