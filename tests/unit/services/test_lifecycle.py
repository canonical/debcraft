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
"""Tests for debcraft's lifecycle service."""

import pytest
from craft_application.models import VersionStr
from debcraft import errors
from debcraft.services import lifecycle


@pytest.mark.parametrize(
    ("deb_format", "version", "is_native"),
    [
        # No format nor version
        pytest.param(None, None, False, id="none-non-native"),
        # Only version
        pytest.param(None, "1.0", True, id="version-native"),
        pytest.param(None, "1.0-1", False, id="version-non-native"),
        # Only format
        pytest.param("3.0 (native)", None, True, id="format-native"),
        pytest.param("3.0 (quilt)", None, False, id="format-quilt"),
        pytest.param("3.0 (other)", None, False, id="format-other"),
        # Consistent format and version
        pytest.param("3.0 (native)", "1.0", True, id="both-native"),
        pytest.param("3.0 (quilt)", "1.0-1", False, id="both-quilt-native"),
        pytest.param("3.0 (other)", "1.0", True, id="both-other-native"),
        pytest.param("3.0 (other)", "1.0-1", False, id="both-other-non-native"),
        # Inconsistent format and version
        pytest.param(
            "3.0 (native)", "1.0-1", None, id="native-format-non-native-version"
        ),
        pytest.param("3.0 (quilt)", "1.0", None, id="quilt-format-native-version"),
    ],
)
def test_is_native_package(
    tmp_path,
    deb_format: str | None,
    version: VersionStr | None,
    *,
    is_native: bool | None,
):
    if deb_format is not None:
        format_file = tmp_path / "debian" / "source" / "format"
        format_file.parent.mkdir(exist_ok=True, parents=True)
        format_file.write_text(deb_format)

    if is_native is not None:
        assert lifecycle._is_native_package(tmp_path, version) == is_native
    else:
        with pytest.raises(errors.DebcraftError, match="Mismatch"):
            lifecycle._is_native_package(tmp_path, version)
