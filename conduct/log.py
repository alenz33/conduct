# *****************************************************************************
# conduct - CONvenient Construction Tool
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Module authors:
#   Alexander Lenz <alexander.lenz@frm2.tum.de>
#
# *****************************************************************************

import logging


## Logging namespaces
BUILDSTEP = 'Step'
CHAIN = 'Chain'
SYSTEM = 'System'


class ConductLog(logging.LoggerAdapter):

    def __init__(self, name, namespace=None):
        logging.LoggerAdapter.__init__(self, logging, {})

        self._format = self._buildFormat(name, namespace)


    def _buildFormat(self, name, namespace):
        fmt = '['

        if namespace is not None:
            fmt += '%s|' % namespace
        fmt += '%s]: ' % name
        fmt += '%s'

        return fmt

    def process(self, msg, kwargs):
        return self._format % msg, kwargs