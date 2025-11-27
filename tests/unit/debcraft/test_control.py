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
"""Unit tests for the Debian control file encoder."""

from io import StringIO

import pytest
from debcraft import control, models


class TestEncoder:
    """Tests for the Encoder class."""

    @pytest.fixture
    def minimal_control(self) -> models.DebianControl:
        """Create a minimal DebianControl instance."""
        return models.DebianControl(
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

    def test_encode_simple_fields(self, minimal_control: models.DebianControl):
        """Test encoding simple string and integer fields."""
        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(minimal_control)

        result = output.getvalue()

        assert "Package: test-package\n" in result
        assert "Source: test-source\n" in result
        assert "Version: 1.0.0\n" in result
        assert "Architecture: amd64\n" in result
        assert "Maintainer: Test User <test@example.com>\n" in result
        assert "Installed-Size: 1024\n" in result
        assert "Section: libs\n" in result
        assert "Priority: optional\n" in result
        assert "Description: A test package\n" in result

    def test_encode_none_fields_excluded(self, minimal_control: models.DebianControl):
        """Test that None fields are not included in output."""
        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(minimal_control)

        result = output.getvalue()

        # These optional fields should not be in the output
        assert "Depends:" not in result
        assert "Recommends:" not in result
        assert "Conflicts:" not in result
        assert "Original-Maintainer:" not in result
        assert "Uploaders:" not in result

    def test_encode_list_fields(self):
        """Test encoding list fields as comma-separated values."""
        ctrl = models.DebianControl(
            package="test-package",
            source="test-source",
            version="1.0.0",
            architecture=["amd64", "arm64", "armhf"],
            maintainer="Test User <test@example.com>",
            installed_size=512,
            depends=["libc6", "libssl3", "python3"],
            recommends=["vim", "emacs"],
            section="libs",
            priority="optional",
            description="A multi-arch package",
        )

        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(ctrl)

        result = output.getvalue()

        assert "Architecture: amd64, arm64, armhf\n" in result
        assert "Depends: libc6, libssl3, python3\n" in result
        assert "Recommends: vim, emacs\n" in result

    def test_encode_multiline_description(self):
        """Test encoding multi-line descriptions with proper formatting."""
        ctrl = models.DebianControl(
            package="test-package",
            source="test-source",
            version="1.0.0",
            architecture="amd64",
            maintainer="Test User <test@example.com>",
            installed_size=256,
            section="libs",
            priority="optional",
            description="Short description\nFirst extended line\nSecond extended line",
        )

        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(ctrl)

        result = output.getvalue()

        # First line with field name
        assert "Description: Short description\n" in result
        # Continuation lines with leading space
        assert " First extended line\n" in result
        assert " Second extended line\n" in result

    def test_encode_multiline_with_empty_lines(self):
        """Test encoding multi-line text with empty lines replaced by dot."""
        ctrl = models.DebianControl(
            package="test-package",
            source="test-source",
            version="1.0.0",
            architecture="amd64",
            maintainer="Test User <test@example.com>",
            installed_size=256,
            section="libs",
            priority="optional",
            description="Short description\nFirst paragraph\n\nSecond paragraph",
        )

        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(ctrl)

        result = output.getvalue()

        # Empty lines should be replaced with " ."
        assert "Description: Short description\n" in result
        assert " First paragraph\n" in result
        assert " .\n" in result
        assert " Second paragraph\n" in result

    def test_encode_field_aliases(self, minimal_control: models.DebianControl):
        """Test that field aliases are properly used in output."""
        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(minimal_control)

        result = output.getvalue()

        # Check that underscored field names are converted to hyphenated aliases
        assert "Installed-Size:" in result
        # Original Python field names should not appear
        assert "installed_size:" not in result

    def test_encode_with_original_maintainer(self):
        """Test encoding with Original-Maintainer field."""
        ctrl = models.DebianControl(
            package="test-package",
            source="test-source",
            version="1.0.0",
            architecture="amd64",
            maintainer="Ubuntu Dev <ubuntu@example.com>",
            installed_size=100,
            section="libs",
            priority="optional",
            description="Test",
            original_maintainer="Debian Dev <debian@example.com>",
        )

        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(ctrl)

        result = output.getvalue()

        assert "Original-Maintainer: Debian Dev <debian@example.com>\n" in result

    def test_encode_with_uploaders_list(self):
        """Test encoding with Uploaders list field."""
        ctrl = models.DebianControl(
            package="test-package",
            source="test-source",
            version="1.0.0",
            architecture="amd64",
            maintainer="Main <main@example.com>",
            installed_size=100,
            section="libs",
            priority="optional",
            description="Test",
            uploaders=["User1 <user1@example.com>", "User2 <user2@example.com>"],
        )

        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(ctrl)

        result = output.getvalue()

        assert (
            "Uploaders: User1 <user1@example.com>, User2 <user2@example.com>\n"
            in result
        )

    def test_encode_full_output_format(self, minimal_control: models.DebianControl):
        """Test that the complete output has expected format."""
        output = StringIO()
        encoder = control.Encoder(output)
        encoder.encode(minimal_control)

        result = output.getvalue()
        lines = result.strip().split("\n")

        # Each line should be a valid control file line (Key: Value format)
        for line in lines:
            if not line.startswith(" "):  # Skip continuation lines
                assert ": " in line, f"Invalid line format: {line}"
