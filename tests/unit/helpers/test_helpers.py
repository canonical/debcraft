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

"""Tests for debcraft's helpers subsystem."""

from pathlib import Path

import pytest
from debcraft.helpers import helpers


class MyHelper(helpers.Helper):
    def run(self) -> None:
        pass


class MyGroup(helpers.HelperGroup):
    def _register(self):
        self._register_helper("test", MyHelper)


def test_get_helper():
    group = MyGroup()
    test_helper = group.get_helper("test")
    assert isinstance(test_helper, MyHelper)


def test_get_helper_error():
    group = MyGroup()
    with pytest.raises(ValueError, match="helper .* is not registered"):
        group.get_helper("does-not-exist")


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        pytest.param(None, {}, id="missing-dir"),
        pytest.param([], {}, id="empty-dir"),
        pytest.param(["docs"], {"myproject": "docs"}, id="default-file"),
        pytest.param(["pkg1.docs"], {"pkg1": "pkg1.docs"}, id="package-file"),
        pytest.param(
            ["docs", "pkg1.docs"],
            {"myproject": "docs", "pkg1": "pkg1.docs"},
            id="default-and-package-file",
        ),
        pytest.param(
            ["pkg1.docs", "pkg2.docs"],
            {"pkg1": "pkg1.docs", "pkg2": "pkg2.docs"},
            id="multiple-package-files",
        ),
    ],
)
def test_build_file_map(tmp_path, files, expected):
    debian_dir = tmp_path / "debian"
    if files is not None:
        debian_dir.mkdir()
        for filename in files:
            (debian_dir / filename).write_text("content")
    result = helpers._build_file_map("docs", "myproject", [debian_dir])
    assert result == {k: debian_dir / v for k, v in expected.items()}


@pytest.mark.parametrize(
    ("source_files", "package", "expected_content"),
    [
        pytest.param(
            {"debcraft/docs": "content"},
            "fake-project",
            "content",
            id="debcraft-default",
        ),
        pytest.param(
            {"debian/docs": "content"},
            "fake-project",
            "content",
            id="debian-default",
        ),
        pytest.param(
            {"debcraft/package-1.docs": "content"},
            "package-1",
            "content",
            id="debcraft-package",
        ),
        pytest.param(
            {"debian/package-1.docs": "content"},
            "package-1",
            "content",
            id="debian-package",
        ),
        pytest.param(
            {"debcraft/docs": "debcraft content", "debian/docs": "debian content"},
            "fake-project",
            "debcraft content",
            id="debcraft-priority",
        ),
    ],
)
def test_install_package_data(
    tmp_path, default_project, source_files, package, expected_content
):
    build_dir = tmp_path / "build"
    install_dir = tmp_path / "install"
    install_dir.mkdir(parents=True)
    dest_dir = Path("usr/share/doc")

    for rel_path, content in source_files.items():
        source_file = build_dir / rel_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(content)

    install_dirs = {f"package/{package}": install_dir}

    helpers.install_package_data(
        name="docs",
        project=default_project,
        dest_dir=dest_dir,
        build_dir=build_dir,
        install_dirs=install_dirs,
    )

    expected = install_dir / dest_dir / package
    assert expected.exists()
    assert expected.read_text() == expected_content
    assert oct(expected.stat().st_mode)[-3:] == "644"


@pytest.mark.parametrize(
    ("install_dirs_keys", "source_files"),
    [
        pytest.param(
            ["default", "build"],
            ["debian/docs"],
            id="skip-default-build",
        ),
        pytest.param(
            ["package/fake-project"],
            [],
            id="no-matching-file",
        ),
    ],
)
def test_install_package_data_nothing_installed(
    tmp_path, default_project, install_dirs_keys, source_files
):
    build_dir = tmp_path / "build"
    dest_dir = Path("usr/share/doc")

    for rel_path in source_files:
        source_file = build_dir / rel_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("content")

    install_dirs = {}
    for key in install_dirs_keys:
        install_dir = tmp_path / key.replace("/", "_")
        install_dir.mkdir(parents=True, exist_ok=True)
        install_dirs[key] = install_dir

    helpers.install_package_data(
        name="docs",
        project=default_project,
        dest_dir=dest_dir,
        build_dir=build_dir,
        install_dirs=install_dirs,
    )

    for install_dir in install_dirs.values():
        assert not (install_dir / dest_dir).exists()


@pytest.mark.parametrize(
    ("source_files", "package", "expected_content"),
    [
        pytest.param(
            {"debcraft/triggers": "content"},
            "fake-project",
            "content",
            id="debcraft-default",
        ),
        pytest.param(
            {"debian/triggers": "content"},
            "fake-project",
            "content",
            id="debian-default",
        ),
        pytest.param(
            {"debcraft/package-1.triggers": "content"},
            "package-1",
            "content",
            id="debcraft-package",
        ),
        pytest.param(
            {"debian/package-1.triggers": "content"},
            "package-1",
            "content",
            id="debian-package",
        ),
        pytest.param(
            {
                "debcraft/triggers": "debcraft content",
                "debian/triggers": "debian content",
            },
            "fake-project",
            "debcraft content",
            id="debcraft-priority",
        ),
    ],
)
def test_install_package_control(
    tmp_path, default_project, source_files, package, expected_content
):
    build_dir = tmp_path / "build"
    partition_dir = tmp_path / "partitions"
    install_dir = tmp_path / "install"
    install_dir.mkdir(parents=True)

    for rel_path, content in source_files.items():
        source_file = build_dir / rel_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(content)

    install_dirs = {f"package/{package}": install_dir}

    helpers.install_package_control(
        name="triggers",
        project=default_project,
        build_dir=build_dir,
        partition_dir=partition_dir,
        install_dirs=install_dirs,
    )

    expected = partition_dir / "package" / package / "debcraft_control" / "triggers"
    assert expected.exists()
    assert expected.read_text() == expected_content
    assert oct(expected.stat().st_mode)[-3:] == "644"


@pytest.mark.parametrize(
    ("install_dirs_keys", "source_files"),
    [
        pytest.param(
            ["default", "build"],
            ["debian/triggers"],
            id="skip-default-build",
        ),
        pytest.param(
            ["package/fake-project"],
            [],
            id="no-matching-file",
        ),
    ],
)
def test_install_package_control_nothing_installed(
    tmp_path, default_project, install_dirs_keys, source_files
):
    build_dir = tmp_path / "build"
    partition_dir = tmp_path / "partitions"

    for rel_path in source_files:
        source_file = build_dir / rel_path
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("content")

    install_dirs = {}
    for key in install_dirs_keys:
        install_dir = tmp_path / key.replace("/", "_")
        install_dir.mkdir(parents=True, exist_ok=True)
        install_dirs[key] = install_dir

    helpers.install_package_control(
        name="triggers",
        project=default_project,
        build_dir=build_dir,
        partition_dir=partition_dir,
        install_dirs=install_dirs,
    )

    assert not (partition_dir / "package").exists()
