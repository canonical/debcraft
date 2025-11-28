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
"""Tests for debcraft's lifecycle service."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from debcraft import errors
from debcraft.services.lifecycle import Lifecycle, _get_prime_dirs_from_project


class TestGetPrimeDirsFromProject:
    """Tests for the _get_prime_dirs_from_project helper function."""

    def test_default_prime_dir_only(self):
        """Test with only the default prime directory."""
        mock_project_info = MagicMock()
        mock_project_info.prime_dir = Path("/work/prime")
        mock_project_info.prime_dirs = {}

        result = _get_prime_dirs_from_project(mock_project_info)

        assert result == {None: Path("/work/prime")}

    def test_with_single_package(self):
        """Test with a single package partition."""
        mock_project_info = MagicMock()
        mock_project_info.prime_dir = Path("/work/prime")
        mock_project_info.prime_dirs = {
            "package/my-package": Path("/work/partitions/package/my-package/prime"),
        }

        result = _get_prime_dirs_from_project(mock_project_info)

        assert result == {
            None: Path("/work/prime"),
            "my-package": Path("/work/partitions/package/my-package/prime"),
        }

    def test_with_multiple_packages(self):
        """Test with multiple package partitions."""
        mock_project_info = MagicMock()
        mock_project_info.prime_dir = Path("/work/prime")
        mock_project_info.prime_dirs = {
            "package/package-1": Path("/work/partitions/package/package-1/prime"),
            "package/package-2": Path("/work/partitions/package/package-2/prime"),
            "package/package-3": Path("/work/partitions/package/package-3/prime"),
        }

        result = _get_prime_dirs_from_project(mock_project_info)

        assert result == {
            None: Path("/work/prime"),
            "package-1": Path("/work/partitions/package/package-1/prime"),
            "package-2": Path("/work/partitions/package/package-2/prime"),
            "package-3": Path("/work/partitions/package/package-3/prime"),
        }

    def test_ignores_non_package_partitions(self):
        """Test that non-package partitions are ignored."""
        mock_project_info = MagicMock()
        mock_project_info.prime_dir = Path("/work/prime")
        mock_project_info.prime_dirs = {
            "package/my-package": Path("/work/partitions/package/my-package/prime"),
            "other/partition": Path("/work/partitions/other/partition/prime"),
            None: Path("/work/prime"),  # Default partition key
        }

        result = _get_prime_dirs_from_project(mock_project_info)

        assert result == {
            None: Path("/work/prime"),
            "my-package": Path("/work/partitions/package/my-package/prime"),
        }

    def test_empty_partition_is_ignored(self):
        """Test that empty string partitions are ignored."""
        mock_project_info = MagicMock()
        mock_project_info.prime_dir = Path("/work/prime")
        mock_project_info.prime_dirs = {
            "": Path("/work/partitions/empty/prime"),
            "package/my-package": Path("/work/partitions/package/my-package/prime"),
        }

        result = _get_prime_dirs_from_project(mock_project_info)

        assert result == {
            None: Path("/work/prime"),
            "my-package": Path("/work/partitions/package/my-package/prime"),
        }


class TestLifecycleGetPrimeDir:
    """Tests for the Lifecycle.get_prime_dir method."""

    @pytest.fixture
    def mock_lifecycle(self):
        """Create a mock Lifecycle service with mocked internals."""
        lifecycle = MagicMock(spec=Lifecycle)
        lifecycle.get_prime_dir = Lifecycle.get_prime_dir.__get__(lifecycle, Lifecycle)
        return lifecycle

    def test_get_default_prime_dir(self, mock_lifecycle):
        """Test getting the default prime directory with None."""
        mock_lifecycle.prime_dirs = {
            None: Path("/work/prime"),
            "my-package": Path("/work/partitions/package/my-package/prime"),
        }

        result = mock_lifecycle.get_prime_dir()

        assert result == Path("/work/prime")

    def test_get_default_prime_dir_explicit_none(self, mock_lifecycle):
        """Test getting the default prime directory with explicit None."""
        mock_lifecycle.prime_dirs = {
            None: Path("/work/prime"),
            "my-package": Path("/work/partitions/package/my-package/prime"),
        }

        result = mock_lifecycle.get_prime_dir(package=None)

        assert result == Path("/work/prime")

    def test_get_package_prime_dir(self, mock_lifecycle):
        """Test getting a package's prime directory."""
        mock_lifecycle.prime_dirs = {
            None: Path("/work/prime"),
            "my-package": Path("/work/partitions/package/my-package/prime"),
        }

        result = mock_lifecycle.get_prime_dir(package="my-package")

        assert result == Path("/work/partitions/package/my-package/prime")

    def test_get_nonexistent_package_raises_error(self, mock_lifecycle):
        """Test that getting a non-existent package raises DebcraftError."""
        mock_lifecycle.prime_dirs = {
            None: Path("/work/prime"),
            "my-package": Path("/work/partitions/package/my-package/prime"),
        }

        with pytest.raises(errors.DebcraftError) as exc_info:
            mock_lifecycle.get_prime_dir(package="nonexistent")

        assert "nonexistent" in str(exc_info.value)
        assert "does not exist" in str(exc_info.value)


class TestLifecyclePrimeDirs:
    """Tests for the Lifecycle.prime_dirs property."""

    def test_prime_dirs_returns_project_info_mapping(self):
        """Test that prime_dirs returns the correct mapping from project info."""
        mock_lifecycle = MagicMock(spec=Lifecycle)
        mock_project_info = MagicMock()
        mock_project_info.prime_dir = Path("/work/prime")
        mock_project_info.prime_dirs = {
            "package/package-1": Path("/work/partitions/package/package-1/prime"),
        }

        # Set up the mock lifecycle manager
        mock_lifecycle._lcm = MagicMock()
        mock_lifecycle._lcm.project_info = mock_project_info

        # Bind the property to our mock
        result = Lifecycle.prime_dirs.fget(mock_lifecycle)

        assert result == {
            None: Path("/work/prime"),
            "package-1": Path("/work/partitions/package/package-1/prime"),
        }
