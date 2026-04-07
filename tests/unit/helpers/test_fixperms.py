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

"""Tests for debcraft's fixperms helper."""

import pathlib
from unittest.mock import call

import pytest
from debcraft.helpers import fixperms


@pytest.mark.parametrize(
    ("file", "perms", "content", "fixed_perms"),
    [
        pytest.param("bin/foo", 0o644, None, 0o755, id="bin"),
        pytest.param("usr/bin/foo", 0o644, None, 0o755, id="usr-bin"),
        pytest.param("usr/games/foo", 0o644, None, 0o755, id="usr-games"),
        pytest.param("sbin/foo", 0o644, None, 0o755, id="sbin"),
        pytest.param("usr/sbin/foo", 0o644, None, 0o755, id="usr-sbin"),
        pytest.param("etc/init.d/foo", 0o644, None, 0o755, id="etc-initd"),
        pytest.param("usr/libexec/foo", 0o644, None, 0o755, id="usr-libexec"),
        pytest.param("etc/foo", 0o755, None, 0o644, id="other-file"),
        pytest.param("usr/share/man/man1/foo.1", 0o755, None, 0o644, id="man-page"),
        pytest.param("usr/share/doc/foo/README", 0o755, None, 0o644, id="doc"),
        pytest.param("usr/lib/foo.so.2", 0o755, None, 0o644, id="shlib"),
        pytest.param("usr/lib/nodejs/cli.js", 0o755, None, 0o644, id="nodejs"),
        pytest.param("usr/lib/nodejs/x/cli.js", 0o644, None, 0o755, id="nodejs-cli"),
        pytest.param("usr/lib/nodejs/x/bin.js", 0o644, None, 0o755, id="nodejs-bin"),
        pytest.param("etc/sudoers.d/foo", 0o644, None, 0o440, id="etc-sudoersd"),
    ],
)
def test_run(mocker, tmp_path, file, perms, content, fixed_perms):
    mock_chown = mocker.patch("debcraft.helpers.fixperms.os.chown")

    path = tmp_path / file
    path.parent.mkdir(parents=True, exist_ok=True)

    if content:
        path.write_bytes(content)
    else:
        path.touch()

    path.chmod(perms)

    helper = fixperms.Fixperms()
    helper.run(prime_dir=tmp_path)

    assert path.stat().st_mode & 0o7777 == fixed_perms

    rel_path = pathlib.Path(file)
    calls = [
        call(tmp_path / x, 0, 0)
        for x in [*list(reversed(rel_path.parents))[1:], rel_path]
    ]
    mock_chown.assert_has_calls(calls)
