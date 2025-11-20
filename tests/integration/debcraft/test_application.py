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

"""Integration tests for the application as a whole."""

import tarfile
from textwrap import dedent
from typing import cast

import craft_application
import debcraft
import pytest
import yaml
from craft_parts import errors
from craft_parts.utils import os_utils
from debcraft import models, services


def is_ubuntu_series(series: str) -> bool:
    """Return true if the current platform is the given Ubuntu series."""
    release = os_utils.OsRelease()
    try:
        return release.id() == "ubuntu" and release.version_id() == series
    except errors.OsReleaseIdError:
        return False


noble_only = pytest.mark.skipif(
    not is_ubuntu_series("24.04"), reason="platform must be ubuntu 24.04"
)


def check_metadata(
    *,
    metadata: models.Metadata,
    project: models.Project,
    arch: str,
) -> None:
    assert metadata.name == project.name
    assert metadata.version == project.version
    assert metadata.architecture == arch


@noble_only
def test_debcraft_pack_clean(monkeypatch, tmp_path, host_architecture: str):
    monkeypatch.setenv("CRAFT_DEBUG", "1")
    monkeypatch.setattr("sys.argv", ["debcraft", "pack", "--destructive-mode"])

    with (tmp_path / "debcraft.yaml").open("w") as project_file:
        project_file.write(
            dedent(f"""\
                name: test-deb
                base: ubuntu@24.04
                version: "1.0"
                platforms:
                    {host_architecture}:

                parts:
                    nil:
                        plugin: nil

        """)
        )

    monkeypatch.chdir(tmp_path)
    services.ServiceFactory.register("package", services.Package)
    app_services = craft_application.ServiceFactory(app=debcraft.METADATA)

    app = debcraft.Application(debcraft.METADATA, app_services)

    result = app.run()

    project = app.services.get("project").get()

    assert result == 0
    assert (tmp_path / "prime").exists()
    assert (tmp_path / "parts").exists()
    assert (tmp_path / "stage").exists()

    metadata_file = tmp_path / "prime/metadata.yaml"
    assert metadata_file.exists()
    metadata = models.Metadata.from_yaml_file(metadata_file)
    project = cast(models.Project, app.services.get("project").get())
    check_metadata(
        metadata=metadata,
        project=project,
        arch=host_architecture,
    )
    assert metadata.base == project.base
    packed_asset = (
        tmp_path / f"{metadata.name}_{metadata.version}_{host_architecture}.tar.xz"
    )
    assert packed_asset.exists()
    with tarfile.open(packed_asset) as tar:
        raw_tar_metadata = tar.extractfile("./metadata.yaml")
        assert raw_tar_metadata is not None
        tar_metadata = models.Metadata.unmarshal(yaml.safe_load(raw_tar_metadata))
    assert tar_metadata == metadata

    monkeypatch.setattr("sys.argv", ["debcraft", "clean", "--destructive-mode"])
    result = app.run()

    assert result == 0

    assert not (tmp_path / "prime").exists()
    assert not (tmp_path / "parts").exists()
    assert not (tmp_path / "stage").exists()
