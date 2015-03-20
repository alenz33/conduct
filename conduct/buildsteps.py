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
#   Alexander Lenz <alexander.lenz@posteo.de>
#
# *****************************************************************************

import conduct
from conduct.util import systemCall

class Parameter(object):
    def __init__(self, type=str, helpStr='Undescribed', required=False, default=None):
        self._type = type
        self._helpStr = helpStr,
        self._required = required
        self._default = default


class BuildStep(object):
    def __init__(self, name):
        self.name = name
        self.log = conduct.log.getChild(name)

    def run(self, args):
        pass


class CopyBS(BuildStep):
    parameters = {
        'source' : Parameter(helpStr='Source to copy', required=True),
        'destination' : Parameter(helpStr='Destination of copy', required=True),
        'recursive' : Parameter(type=bool, helpStr='Copy directories recursively', required=True),
    }

    def run(self, args):
        fromPath = args['source']
        toPath = args['destination']
        recursive = args['recursive']

        cpArgs = '-r' if recursive else ''
        cmd = 'cp %s %s %s' % (cpArgs, fromPath, toPath)

        systemCall(cmd,log=self.log)