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

import subprocess
from textwrap import dedent
from typing import cast

import craft_application
import craft_parts
import debcraft
import distro
import pytest
from debcraft import models, services

HOST_DISTRO = distro.LinuxDistribution()

debian_like_only = pytest.mark.skipif(
    HOST_DISTRO.id() != "debian" and "debian" not in HOST_DISTRO.like(),
    reason="host OS must be debian-like",
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


# The app stops a real emitter, but the testable RecordingEmitter makes stop a no-op.
@pytest.mark.usefixtures("emitter", "reset_parts_features")
@debian_like_only
def test_debcraft_pack_clean(monkeypatch, tmp_path, host_architecture: str):
    monkeypatch.setenv("CRAFT_DEBUG", "1")
    monkeypatch.setattr("sys.argv", ["debcraft", "pack", "--destructive-mode"])

    with (tmp_path / "debcraft.yaml").open("w") as project_file:
        project_file.write(
            dedent(f"""\
                name: test-deb
                base: {HOST_DISTRO.id()}@{HOST_DISTRO.version()}
                version: "1.0"
                summary: A test deb
                description: Just a test deb
                maintainer: Mike Maintainer <maintainer@example.com>
                section: libs

                platforms:
                  {host_architecture}:

                packages:
                  package-1:
                    version: "1.23"

                parts:
                  nil:
                    plugin: nil
        """)
        )

    monkeypatch.chdir(tmp_path)
    services.ServiceFactory.register(
        "project", "Project", module="debcraft.services.project"
    )
    services.ServiceFactory.register(
        "package", "Package", module="debcraft.services.package"
    )
    services.ServiceFactory.register(
        "lifecycle", "Lifecycle", module="debcraft.services.lifecycle"
    )
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
    packed_asset = tmp_path / f"package-1_1.23_{host_architecture}.deb"
    assert packed_asset.exists()

    result = subprocess.run(
        ["ar", "t", str(packed_asset)], check=True, capture_output=True, text=True
    )
    members = result.stdout.strip().splitlines()
    assert members == ["debian-binary", "control.tar.zst", "data.tar.zst"]

    craft_parts.Features.reset()
    monkeypatch.setattr("sys.argv", ["debcraft", "clean", "--destructive-mode"])
    result = app.run()

    assert result == 0

    assert not (tmp_path / "prime").exists()
    assert not (tmp_path / "parts").exists()
    assert not (tmp_path / "stage").exists()
