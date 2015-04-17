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
from conduct.loggers import LOGLEVELS, INVLOGLEVELS
from conduct.param import Parameter, oneof, Referencer

class BuildStepMeta(type):
    '''
    Meta class for merging parameters and outparameters within the
    inheritance tree.
    '''

    def __new__(mcls, name, bases, attrs):
        mcls._storeClsToParams(name, attrs)

        mcls._mergeDictAttr('parameters', bases, attrs)
        mcls._mergeDictAttr('outparameters', bases, attrs)

        mcls._createProperties(attrs['parameters'], attrs)
        mcls._createProperties(attrs['outparameters'], attrs)


        cls = type.__new__(mcls, name, bases, attrs)

        return cls

    @classmethod
    def _storeClsToParams(mcls, name, attrs):
        for param in attrs['parameters'].values():
            param.classname = '%s.%s' % (attrs['__module__'], name)



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
        for name, definition in paramDict.items():
            mcls._createProperty(name, definition, attrs)


    @classmethod
    def _createProperty(mcls, paramName, paramDef, attrs):
        capitalParamName = paramName.capitalize()

        # set default value for parameter
        #if paramDef.default is not None:
        #    attrs['_params'][paramName] = paramDef.default

        # create parameter read function
        def readFunc(self):
            if hasattr(self, 'doRead%s' % capitalParamName):
                return getattr(self, 'doRead%s' % capitalParamName)()

            value = self._params.get(paramName, paramDef.default)

            # resolve references
            if isinstance(value, Referencer):
                # resolve and validate
                value = paramDef.type(value.evaluate(self.chain))

            return value
        readFunc.__name__ = '_readParam%s' % capitalParamName

        # create parameter write function
        def writeFunc(self, value):
            try:
                validValue = paramDef.type(value)
                if hasattr(self, 'doWrite%s' % capitalParamName):
                    getattr(self, 'doWrite%s' % capitalParamName)(validValue)
                else:
                    # special handling for references
                    if not isinstance(value, Referencer):
                        value = paramDef.type(value)
                    self._params[paramName] = value
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
        'retries' : Parameter(type=int,
                                  description='Number of retries to execute the '
                                    'build step',
                                  default=0),
    }

    outparameters = {
    }

    def __init__(self, name, paramValues, chain=None):
        self.name = name
        self.chain = chain # Maintain a reference to the chain (for refs)
        self.wasRun = False

        self._params = {}

        self._initLogger()
        self._applyParams(paramValues)


    def build(self):
        '''
        Build the build step.
        This method is a wrapper around run() that does some logging and
        exception handling.
        '''
        # log some bs stuff
        self.log.info('=' * 80)
        self.log.info('Build: %s' % self.name)
        self.log.info(self.description)
        self.log.info('-' * 80)

        success = False

        for i in range(0, self.retries +1):
            try:
                # execute actual build actions
                self.run()
                self.wasRun = True
                success = True
                break
            except Exception as exc:
                self.log.exception(exc)

                # handle retries
                if self.retries > i:
                    self.log.warn('Failed; Retry %s/%s' % (i+1, self.retries))

        # log some bs stuff
        self.log.info('')
        self.log.info('%s' % 'SUCCESS' if success else 'FAILED')
        self.log.info('')

        if not success:
            raise RuntimeError('Build step failed')

    def cleanupBuild(self):
        '''
        Cleanup all the build step's leftovers.
        his method is a wrapper around cleanup() that does some logging and
        exception handling.
        '''

        if not self.wasRun:
            self.log.info('Cleanup: Step was not run; Skip')
            return

        if self.cleanup.im_func == BuildStep.cleanup.im_func:
            self.log.info('Cleanup: No custom cleanup; Skip')
            return

        self.log.info('=' * 80)
        self.log.info('Cleanup: %s' % self.name)
        self.log.info(self.description)
        self.log.info('-' * 80)

        resultStr = 'SUCCESS'
        try:
            self.cleanup()
            self.wasRun = False
        except Exception as exc:
            resultStr = 'FAILED'
            self.log.exception(exc)

            raise
        finally:
            self.log.info('')
            self.log.info('%s' % resultStr)
            self.log.info('')


    def cleanup(self):
        '''
        This function shall be overwritten by the specific build steps
        and should do everything that's necessary for cleaning up after
        the build.
        '''
        pass


    def run(self):
        '''
        This function shall be overwritten by the specific build steps
        and should do everything that's necessary build this step.
        '''
        raise NotImplemented('Buildstep not implemented (may be abstract)')

    def doWriteLoglevel(self, value):
        self.log.setLevel(LOGLEVELS[value])

    def doReadLoglevel(self):
        level = self.log.getEffectiveLevel()
        return INVLOGLEVELS[level]

    def _initLogger(self):
        if self.chain is not None:
            self.log = self.chain.log.getChild(self.name)
        else:
            self.log = conduct.log.getChild(self.name)
        self.log.setLevel(LOGLEVELS[self.loglevel])

    def _applyParams(self, paramValues):

        for name, paramDef in self.parameters.items():
            if name in paramValues:
                setattr(self, name, paramValues[name])
            elif paramDef.default is None:
                raise RuntimeError('%s: Mandatory parameter %s is missing'
                                   % (self.name, name))