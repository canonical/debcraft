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

"""Tests for debcraft's compress helper."""

import gzip
import os
from pathlib import Path

import pytest
from debcraft.helpers import compress

_IMAGE_FILES = ("image.jpg", "image.jpeg", "image.gif", "image.png")
_COMPRESSED_FILES = ("file.gz", "file.xz", "file.zip", "file.bz2", "file.z")


@pytest.mark.parametrize(
    ("dirname", "expected", "exclusions"),
    [
        ("usr/share/doc", True, ("copyright", *_IMAGE_FILES, *_COMPRESSED_FILES)),
        ("usr/share/man/man1", True, _IMAGE_FILES),
        ("usr/share/info", True, _IMAGE_FILES),
        ("usr/bin", False, ()),
    ],
)
def test_compress_run(tmp_path, dirname, expected, exclusions):
    subdir = tmp_path / dirname
    subdir.mkdir(parents=True, exist_ok=True)

    primary = subdir / "file1.txt"
    with primary.open("wb") as f:
        f.truncate(5000)

    linked = subdir / "file2.txt"
    os.link(primary, linked)

    symlinked = subdir / "symlink.txt"
    symlinked.symlink_to(primary.name)

    for excluded in exclusions:
        with (subdir / excluded).open("wb") as f:
            f.truncate(5000)

    helper = compress.Compress()
    helper.run(prime_dir=tmp_path)

    primary_gz = subdir / "file1.txt.gz"
    linked_gz = subdir / "file2.txt.gz"
    symlinked_gz = subdir / "symlink.txt.gz"

    if expected:
        # Check that .gz files exist and original files are gone
        assert primary_gz.is_file()
        assert linked_gz.is_file()
        assert symlinked_gz.is_symlink()
        assert not primary.exists()
        assert not linked.exists()
        assert not symlinked.exists()

        # Verify they are still hard links
        assert primary_gz.stat().st_ino == linked_gz.stat().st_ino

        # Verify the symlink destination
        assert symlinked_gz.readlink() == Path(primary_gz.name)
    else:
        # Files were not compressed
        assert not primary_gz.exists()
        assert not linked_gz.exists()
        assert not symlinked_gz.exists()
        assert primary.is_file()
        assert linked.is_file()
        assert symlinked.is_symlink()

    for excluded in exclusions:
        assert (subdir / excluded).is_file()
        assert not (subdir / (excluded + ".gz")).exists()


def test_compress_group(tmp_path):
    primary = tmp_path / "file1.txt"
    primary.write_text("hello world")

    linked = tmp_path / "file2.txt"
    os.link(primary, linked)

    group = [primary, linked]
    compress._compress_group(group, tmp_path)

    primary_gz = tmp_path / "file1.txt.gz"
    linked_gz = tmp_path / "file2.txt.gz"

    # Check that .gz files exist and original files are gone
    assert primary_gz.is_file()
    assert linked_gz.is_file()
    assert not primary.exists()
    assert not linked.exists()

    # Verify compression
    with gzip.open(primary_gz, "rt") as f:
        assert f.read() == "hello world"

    # Verify they are still hard links
    assert primary_gz.stat().st_ino == linked_gz.stat().st_ino


@pytest.mark.parametrize(
    ("link_name", "target_val", "is_absolute"),
    [
        # Absolute link: points to /usr/share/man/man1/ls.1
        pytest.param(
            "usr/bin/ls-link", "/usr/share/man/man1/ls.1", True, id="absolute"
        ),
        # Relative link: README.txt points to README in the same dir
        pytest.param("usr/share/doc/pkg/README.txt", "README", False, id="relative"),
    ],
)
def test_fix_symlinks(tmp_path, link_name, target_val, is_absolute):
    root = tmp_path / "root"
    root.mkdir()

    # Define the actual file that "exists" in our build
    # For absolute test: usr/share/man/man1/ls.1
    # For relative test: usr/share/doc/pkg/README
    if is_absolute:
        real_file_path = root / Path(target_val).relative_to("/")
    else:
        real_file_path = (root / Path(link_name).parent / target_val).resolve()

    real_file_path.parent.mkdir(parents=True, exist_ok=True)
    real_file_path.touch()

    # Create the symlink
    link_path = root / link_name
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(target_val)

    # Fix symlinks
    compressed_files = {real_file_path}
    compress._fix_symlinks([link_path], compressed_files, root)

    # Verify the link now points to the .gz version of the target filename
    expected_target = Path(target_val).parent / (Path(target_val).name + ".gz")
    link_gz_path = link_path.parent / (link_path.name + ".gz")
    assert link_gz_path.readlink() == Path(expected_target)


def test_fix_symlink_chain(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    file = tmp_path / "file"
    link1 = tmp_path / "link1"
    link2 = tmp_path / "subdir/link2"
    link3 = tmp_path / "link3"
    link4 = tmp_path / "link4"
    filegz = tmp_path / "file.gz"

    link1.symlink_to("file")
    link2.symlink_to("../link1")
    link3.symlink_to("link1")
    link4.symlink_to("/subdir/link2")
    filegz.touch()

    compressed_files = {file}
    compress._fix_symlinks([link1, link2, link3, link4], compressed_files, tmp_path)

    assert (tmp_path / "file.gz").exists()
    assert (tmp_path / "link1.gz").is_symlink()
    assert (tmp_path / "link1.gz").readlink() == Path("file.gz")
    assert (tmp_path / "subdir/link2.gz").is_symlink()
    assert (tmp_path / "subdir/link2.gz").readlink() == Path("../link1.gz")
    assert (tmp_path / "link3.gz").is_symlink()
    assert (tmp_path / "link3.gz").readlink() == Path("link1.gz")
    assert (tmp_path / "link4.gz").is_symlink()
    assert (tmp_path / "link4.gz").readlink() == Path("/subdir/link2.gz")


@pytest.mark.parametrize(
    ("path_str", "size", "expected"),
    [
        # Hard Exclusions
        pytest.param("usr/share/doc/copyright", 5000, False, id="copyright-exclusion"),
        pytest.param("usr/share/doc/file.jpg", 5000, False, id="jpg-exclusion"),
        pytest.param("usr/share/doc/file.png", 5000, False, id="png-exclusion"),
        pytest.param("usr/share/doc/file.pdf", 5000, False, id="pdf-exclusion"),
        pytest.param("usr/share/doc/file.zip", 5000, False, id="zip-exclusion"),
        pytest.param("usr/share/doc/file.gz", 5000, False, id="gz-exclusion"),
        # Mandatory Compression (man/info)
        pytest.param("usr/share/man/man1/ls.1", 100, True, id="man-page"),
        pytest.param("usr/share/info/file", 100, True, id="info-file"),
        # Changelogs
        pytest.param("usr/share/doc/pkg/changelog", 100, True, id="changelog"),
        pytest.param(
            "usr/share/doc/pkg/changelog.Debian", 100, True, id="changelog-debian"
        ),
        pytest.param(
            "usr/share/doc/pkg/CHANGELOG.html", 100, True, id="changelog-uppercase"
        ),
        # Documentation size threshold
        pytest.param(
            "usr/share/doc/pkg/README", 4097, True, id="large-readme"
        ),  # > 4kb
        pytest.param("usr/share/doc/pkg/README", 4096, False, id="small-readme"),
        # Random file outside policy
        pytest.param("usr/bin/binary", 5000, False, id="other-file"),
    ],
)
def test_should_compress(tmp_path, path_str, size, expected):
    path = tmp_path / path_str
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as f:
        f.truncate(size)

    assert compress._should_compress(path, tmp_path) == expected
