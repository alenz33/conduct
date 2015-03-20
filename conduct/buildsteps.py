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

import conduct
from conduct.util import systemCall
from conduct.loggers import LOGLEVELS, INVLOGLEVELS
from conduct.param import Parameter, oneof


class BuildStepMeta(type):
    '''
    Meta class for merging parameters and outparameters within the
    inheritance tree.
    '''

    def __new__(mcls, name, bases, attrs):
        mcls._mergeDictAttr('parameters', bases, attrs)
        mcls._mergeDictAttr('outparameters', bases, attrs)

        attrs['_params'] = {}
        mcls._createProperties(attrs['parameters'], attrs)
        mcls._createProperties(attrs['outparameters'], attrs)


        cls = type.__new__(mcls, name, bases, attrs)

        return cls

    @classmethod
    def _mergeDictAttr(mcls, name, bases, attrs):
        attr = {}

        for base in bases:
            if hasattr(base, name):
                attr.update(getattr(base, name))

        attr.update(attrs.get(name, {}))

        attrs[name] = attr

    @classmethod
    def _createProperties(mcls, paramDict, attrs):
        for name, definition in paramDict.iteritems():
            mcls._createProperty(name, definition, attrs)


    @classmethod
    def _createProperty(mcls, paramName, paramDef, attrs):
        capitalParamName = paramName.capitalize()

        # set default value for parameter
        if paramDef.default is not None:
            attrs['_params'][paramName] = paramDef.default

        # create parameter read function
        def readFunc(self):
            if hasattr(self, 'doRead%s' % capitalParamName):
                return getattr(self, 'doRead%s' % capitalParamName)()
            return self._params[paramName]
        readFunc.__name__ = '_readParam%s' % capitalParamName

        # create parameter write function
        def writeFunc(self, value):
            try:
                validValue = paramDef.type(value)
                if hasattr(self, 'doWrite%s' % capitalParamName):
                    getattr(self, 'doWrite%s' % capitalParamName)(validValue)
                else:
                    self._params[paramName] = paramDef.type(value)
            except ValueError as e:
                raise ValueError('Cannot set %s: %s' % (paramName, e))
        writeFunc.__name__ = '_writeParam%s' % capitalParamName
        # create parameter property
        attrs[paramName] = property(readFunc, writeFunc)


class BuildStep(object):
    __metaclass__ = BuildStepMeta

    parameters = {
        'description' : Parameter(type=str,
                                  description='Build step description',
                                  default='Undescribed'),
        'loglevel' : Parameter(type=oneof(LOGLEVELS.keys()),
                               description='Log level',
                               default='info'),
    }

    outparameters = {
    }

    def __init__(self, name, paramCfg):
        self._paramCfg = paramCfg

        self.name = name

        self._initLogger()


    def build(self):
        # log some bs stuff
        self.log.info('=' * 80)
        self.log.info('Start build step: %s' % self.name)
        self.log.info(self.description)
        self.log.info('-' * 80)

        resultStr = 'SUCCESS'
        try:
            # execute actual build actions
            self.run({})
        except Exception as exc:
            resultStr = 'FAILED'
            self.log.exception(exc)

            return False
        finally:
            self.log.info('')
            self.log.info('%s' % resultStr)
            self.log.info('=' * 80)

        return True


    def run(self, args):
        pass

    def doWriteLoglevel(self, value):
        self.log.setLevel(LOGLEVELS[value])

    def doReadLoglevel(self):
        level = self.log.getEffectiveLevel()
        return INVLOGLEVELS[level]


    def _initLogger(self):
        self.log = conduct.log.getChild(self.name)

        loglevel = self._paramCfg.get('loglevel',
                                      self.parameters['loglevel'].default)
        self.log.setLevel(LOGLEVELS[loglevel])


class CopyBS(BuildStep):
    parameters = {
        'source' : Parameter(type=str, description='Source to copy'),
        'destination' : Parameter(type=str, description='Destination of copy'),
        'recursive' : Parameter(type=bool, description='Copy directories recursively'),
    }

    def run(self, args):
        fromPath = args['source']
        toPath = args['destination']
        recursive = args['recursive']

        cpArgs = '-r' if recursive else ''
        cmd = 'cp %s %s %s' % (cpArgs, fromPath, toPath)

        systemCall(cmd,log=self.log)