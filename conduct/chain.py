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

import re
from os import path
from collections import OrderedDict

import conduct
from conduct.param import Parameter
from conduct.util import loadChainDefinition, Referencer, importFromPath


class Chain(object):
    def __init__(self, name, paramValues):
        self.name = name
        self.steps = OrderedDict()
        self.params = {}

        self._chainDef = {}

        self._initLogger()
        self._loadChainDefinition()
        self._applyParamValues(paramValues)


    def build(self):
        try:
            for step in self.steps.values():
                step.build()
        except Exception as e:
            self.log.error('BUILD FAILED')

        for step in reversed(self.steps.values()):
            step.cleanupBuild()


    @property
    def parameters(self):
        return self._chainDef['parameters']

    def _initLogger(self):
        self.log = conduct.log.getChild(self.name, True)

    def _applyParamValues(self, values):
        for name, definition in self.parameters.items():
            if name in values:
                self.params[name] = values[name]
            elif definition.default is not None:
                self.params[name] = definition.default
            else:
                raise RuntimeError('Mandatory parameter %s is missing' % name)

    def _loadChainDefinition(self):
        self._chainDef = loadChainDefinition(self.name)

        # create build steps
        self._createSteps()

    def _createSteps(self):
        for name, definition in self._chainDef['steps'].items():
            # name should be step:name or chain:name
            entryType, entryName = definition[0].split(':')

            if entryType == 'step':
                cls = importFromPath(entryName, ('conduct.buildsteps.',))
                # for steps, the entryName should be a full path (mod.class)
                #clsMod, _, clsName = entryName.rpartition('.')
                #mod = __import__(clsMod)
                #cls = getattr(mod, clsName)

                params = self._createReferencers(definition[1])
                self.steps[name] = cls(name, params, self)
            else:
                # TODO parameter forwarding
                self.steps[name] = Chain(entryName)

    def _createReferencers(self, paramValues):
        for paramName, paramValue in paramValues.items():
            if isinstance(paramValue, str) \
                and re.match('.*?(\{(.*?)\})+.*?', paramValue):
                    paramValues[paramName] = Referencer(paramValue)

        return paramValues




