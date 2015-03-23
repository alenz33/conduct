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

import pprint
from os import path

import conduct
from conduct.param import Parameter
from conduct.util import AttrStringifier, ObjectiveOrderedDict


class Chain(object):
    def __init__(self, name):
        self.name = name
        self._chainDef = {}
        self._steps = []

        self._loadChainFile()


    def build(self):
        for step in self._steps:
            step.build()


    def _loadChainFile(self):
        # determine chain file location
        chainDir = conduct.cfg['conduct']['chaindir']
        chainFile = path.join(chainDir, '%s.py' % self.name)

        if not path.exists(chainFile):
            raise IOError('Chain file for \'%s\' not found (Should be: %s)'
                          % (self.name, chainFile))

        content = open(chainFile).read()

        # prepare exection namespace
        ns = {
            'Parameter' : Parameter,
            'Step' : lambda cls, **params: ('step:%s' % cls, params),
            'Chain' : lambda cls, **params: ('chain:%s' % cls, params),
            'steps' : ObjectiveOrderedDict()
        }

        # execute and extract all the interesting data
        exec content in ns

        for entry in ['description', 'parameters']:
            self._chainDef[entry] = ns[entry]

        self._chainDef['steps'] = ns['steps'].entries

        # create build steps
        self._createSteps()

    def _createSteps(self):
        for name, definition in self._chainDef['steps'].iteritems():
            # name should be step:name or chain:name
            entryType, entryName = definition[0].split(':')

            if entryType == 'step':
                # for steps, the entryName should be a full path (mod.class)
                clsMod, _, clsName = entryName.rpartition('.')
                mod = __import__(clsMod)
                cls = getattr(mod, clsName)

                step = cls(name, definition[1])
                self._steps.append(step)
            else:
                self._steps.append(Chain(entryName))



