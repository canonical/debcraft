#  This file is part of debcraft
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

"""Entrypoint to use if running with python -m debcraft."""

import os
import sys
import warnings

# This needs to happen before we import any external packages.
if not os.getenv("CRAFT_DEBUG"):
    warnings.simplefilter("ignore")

from debcraft.cli import main

sys.exit(main())
