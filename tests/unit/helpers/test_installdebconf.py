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

"""Tests for debcraft's installdebconf helper."""

from pathlib import Path

import pytest
from craft_parts import ProjectInfo
from debcraft.helpers import installdebconf
from debcraft.models import Project


@pytest.mark.parametrize("debian_dir", ["debian"])
@pytest.mark.parametrize(
    ("packages", "files"),
    [
        pytest.param(["fake-project"], ["config", "templates"], id="default"),
        pytest.param(["pkg1", "pkg2"], ["pkg1.config", "pkg1.templates"], id="single"),
        pytest.param(
            ["pkg1", "pkg2"],
            ["pkg1.config", "pkg1.templates", "pkg2.config", "pkg2.templates"],
            id="both",
        ),
    ],
)
def test_run(tmp_path, default_project, debian_dir, packages, files):
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    install_dirs = {}
    for package in packages:
        partition = f"package/{package}"
        install_dirs[partition] = tmp_path / package / "install"
        install_dirs[partition].mkdir(parents=True, exist_ok=True)

    for file in files:
        file_path = build_dir / debian_dir / file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("content")

    project_info = ProjectInfo(
        application_name="project",
        cache_dir=tmp_path / "cache",
        arch="amd64",
        partitions=["partition"],
    )

    helper = installdebconf.Installdebconf()
    helper.run(
        build_dir=build_dir,
        partition_dir=tmp_path,
        project=default_project,
        install_dirs=install_dirs,
        project_info=project_info,
    )

    for package in packages:
        partition = f"package/{package}"
        conf_dir = tmp_path / partition

        file_types_for_package: set[str] = set()
        all_file_types: set[str] = set()

        for conf_file in files:
            if "." not in conf_file:
                file_package = default_project.name
                file_type = conf_file  # "config" or "templates"
            else:
                file_package, _, file_type = conf_file.partition(".")

            all_file_types.add(file_type)
            if package == file_package:
                file_types_for_package.add(file_type)

        for file_type in all_file_types:
            installed_conf_file = conf_dir / "debcraft_control" / file_type
            if file_type in file_types_for_package:
                assert installed_conf_file.exists()
                assert installed_conf_file.read_bytes() == b"content"
            else:
                assert not installed_conf_file.exists()


def test_run_substitutions(
    tmp_path: Path, default_project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOO", "bar")
    packages = ["pkg1", "pkg2"]
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    install_dirs = {}
    for package in packages:
        partition = f"package/{package}"
        install_dirs[partition] = tmp_path / package / "install"
        install_dirs[partition].mkdir(parents=True, exist_ok=True)

    for suffix in (".config", ".templates"):
        for package in packages:
            file = (build_dir / "debian" / package).with_suffix(suffix)
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("#PACKAGE# #DEB_HOST_NAME# #ENV.FOO# #IGNORE_ME#")

    project_info = ProjectInfo(
        application_name="project",
        cache_dir=tmp_path / "cache",
        arch="amd64",
        partitions=["partition"],
    )

    helper = installdebconf.Installdebconf()
    helper.run(
        build_dir=build_dir,
        partition_dir=tmp_path,
        project=default_project,
        install_dirs=install_dirs,
        project_info=project_info,
    )

    for package in packages:
        # Do not substitute content in templates files
        conf_dir = tmp_path / "package" / package / "debcraft_control"
        template = conf_dir / "templates"
        assert template.read_text() == "#PACKAGE# #DEB_HOST_NAME# #ENV.FOO# #IGNORE_ME#"

        # Substitute contents in config files
        # The environment should be read and the #PACKAGE# variable should change
        # per-package being built
        config = conf_dir / "config"
        assert config.read_text() == f"{package} amd64 bar #IGNORE_ME#"
