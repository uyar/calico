# Copyright (C) 2019 H. Turgut Uyar <uyar@itu.edu.tr>
#
# Calico is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Calico is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Calico.  If not, see <http://www.gnu.org/licenses/>.

"""General settings."""

from __future__ import absolute_import, division, print_function, unicode_literals

from distutils.spawn import find_executable


__version__ = "1.1.0.dev0"  # sig: str

GLOBAL_TIMEOUT = 2  # sig: int
"""Default timeout for tests, in seconds."""

SUPPORTS_JAIL = find_executable("fakechroot") is not None  # sig: bool
"""Whether this system supports changing root directory for a process."""
