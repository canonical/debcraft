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
"""Unit tests for the DebianControl model and field alias generation."""

import pytest
from debcraft.models.control import DebianControl, _field_alias


class TestFieldAlias:
    """Tests for the _field_alias function."""

    @pytest.mark.parametrize(
        ("field_name", "expected_alias"),
        [
            ("package", "Package"),
            ("version", "Version"),
            ("architecture", "Architecture"),
            ("installed_size", "Installed-Size"),
            ("original_maintainer", "Original-Maintainer"),
            ("depends", "Depends"),
            ("recommends", "Recommends"),
        ],
    )
    def test_field_alias_generation(self, field_name: str, expected_alias: str):
        """Test that field names are properly converted to Debian control format."""
        assert _field_alias(field_name) == expected_alias


class TestDebianControlModel:
    """Tests for the DebianControl model."""

    @pytest.fixture
    def minimal_control(self) -> DebianControl:
        """Create a minimal DebianControl instance."""
        return DebianControl(
            package="test-package",
            source="test-source",
            version="1.0.0",
            architecture="amd64",
            maintainer="Test User <test@example.com>",
            installed_size=1024,
            section="libs",
            priority="optional",
            description="A test package",
        )

    def test_minimal_control_creation(self, minimal_control: DebianControl):
        """Test creation of a minimal DebianControl instance."""
        assert minimal_control.package == "test-package"
        assert minimal_control.source == "test-source"
        assert minimal_control.version == "1.0.0"
        assert minimal_control.architecture == "amd64"
        assert minimal_control.maintainer == "Test User <test@example.com>"
        assert minimal_control.installed_size == 1024
        assert minimal_control.section == "libs"
        assert minimal_control.priority == "optional"
        assert minimal_control.description == "A test package"

    def test_optional_fields_default_to_none(self, minimal_control: DebianControl):
        """Test that optional fields default to None."""
        assert minimal_control.depends is None
        assert minimal_control.recommends is None
        assert minimal_control.conflicts is None
        assert minimal_control.breaks is None
        assert minimal_control.replaces is None
        assert minimal_control.provides is None
        assert minimal_control.original_maintainer is None
        assert minimal_control.uploaders is None

    def test_control_with_all_optional_fields(self):
        """Test creation of a DebianControl instance with all optional fields."""
        control = DebianControl(
            package="full-package",
            source="full-source",
            version="2.0.0",
            architecture=["amd64", "arm64"],
            maintainer="Main User <main@example.com>",
            installed_size=2048,
            depends=["libc6", "libssl3"],
            recommends=["vim"],
            conflicts=["old-package"],
            breaks=["broken-package"],
            replaces=["replaced-package"],
            provides=["virtual-package"],
            section="utils",
            priority="required",
            description="A full test package",
            original_maintainer="Original User <orig@example.com>",
            uploaders=["Uploader1 <up1@example.com>", "Uploader2 <up2@example.com>"],
        )

        assert control.depends == ["libc6", "libssl3"]
        assert control.recommends == ["vim"]
        assert control.conflicts == ["old-package"]
        assert control.breaks == ["broken-package"]
        assert control.replaces == ["replaced-package"]
        assert control.provides == ["virtual-package"]
        assert control.original_maintainer == "Original User <orig@example.com>"
        assert control.uploaders == [
            "Uploader1 <up1@example.com>",
            "Uploader2 <up2@example.com>",
        ]

    def test_architecture_as_list(self):
        """Test that architecture can be specified as a list."""
        control = DebianControl(
            package="multi-arch-package",
            source="multi-arch-source",
            version="1.0.0",
            architecture=["amd64", "arm64", "armhf"],
            maintainer="Test User <test@example.com>",
            installed_size=512,
            section="libs",
            priority="optional",
            description="Multi-arch package",
        )

        assert control.architecture == ["amd64", "arm64", "armhf"]

    def test_field_alias_in_model_dump(self, minimal_control: DebianControl):
        """Test that field aliases are used in model dump by alias."""
        dumped = minimal_control.model_dump(by_alias=True)

        assert "Package" in dumped
        assert "Source" in dumped
        assert "Version" in dumped
        assert "Architecture" in dumped
        assert "Maintainer" in dumped
        assert "Installed-Size" in dumped
        assert "Section" in dumped
        assert "Priority" in dumped
        assert "Description" in dumped
