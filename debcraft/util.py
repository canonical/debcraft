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

"""Utilities for debcraft."""

import functools
import platform

from debcraft import errors

_ARCH_TRIPLETS = {
    "aarch64": "aarch64-linux-gnu",
    "armv7l": "arm-linux-gnueabihf",
    "ppc64le": "powerpc64le-linux-gnu",
    "riscv64": "riscv64-linux-gnu",
    "s390x": "s390x-linux-gnu",
    "x86_64": "x86_64-linux-gnu",
    "i686": "i386-linux-gnu",
}


@functools.lru_cache
def get_arch_triplet(arch: str | None = None) -> str:
    """Get the arch triplet string for an architecture.

    :param arch: Architecture to get the triplet of. If None, then get the arch triplet
    of the host.

    :returns: The arch triplet.
    """
    if not arch:
        arch = platform.machine()
    arch_triplet = _ARCH_TRIPLETS.get(arch)

    if not arch_triplet:
        raise errors.DebcraftError(f"arch triplet is not defined for arch {arch!r}")

    return arch_triplet
