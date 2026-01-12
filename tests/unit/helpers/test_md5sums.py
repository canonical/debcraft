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

"""Tests for debcraft's md5sums service."""

from debcraft.helpers import md5sums


def test_md5sum(tmp_path):
    foo = tmp_path / "foo.txt"
    foo.write_text("file content")
    result = md5sums._md5sum(foo)
    assert result == "d10b4c3ff123b26dc068d43a8bef2d23"


def test_md5sums(tmp_path):
    test_dir = tmp_path / "dir"
    test_dir.mkdir()
    foo = test_dir / "foo.txt"
    bar = test_dir / "bar.txt"
    foo.write_text("file content")
    bar.write_text("more file content")

    helper = md5sums.Md5sums()
    helper.run(prime_dir=test_dir, control_dir=tmp_path)

    content = (tmp_path / "md5sums").read_text()
    assert "cc4005f23a42e90094a943e9eb5cbce3  bar.txt\n" in content
    assert "d10b4c3ff123b26dc068d43a8bef2d23  foo.txt\n" in content
