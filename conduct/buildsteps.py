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

import os
import time
import hashlib
import ConfigParser
import shutil

from os import path

import conduct
from conduct.util import systemCall, Referencer, ensureDirectory, mount, \
    umount, chrootedSystemCall
from conduct.loggers import LOGLEVELS, INVLOGLEVELS
from conduct.param import Parameter, oneof, none_or, dictof, listof, tupleof

__all__ = ['BuildStep', 'SystemCall', 'Config', 'TmpDir', 'RmPath',
           'Partitioning', 'DevMapper', 'CreateFileSystem', 'Mount',
           'MakeDirs', 'Debootstrap']


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
        self.log.info('Start build step: %s' % self.name)
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
        self.log.info('=' * 80)

        if not success:
            raise RuntimeError('Build step failed')

    def cleanupBuild(self):
        '''
        Cleanup all the build step's leftovers.
        his method is a wrapper around cleanup() that does some logging and
        exception handling.
        '''
        if not self.wasRun:
            return

        self.log.info('=' * 80)
        self.log.info('Cleanup build step: %s' % self.name)
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
            self.log.info('=' * 80)


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
        pass

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


class SystemCall(BuildStep):
    '''
    Build step to execute given shell command.
    '''
    parameters = {
        'command' : Parameter(type=str,
                              description='command to execute'),
        'captureoutput' : Parameter(type=bool,
                                    description='Capture command output',
                                    default=True),
        'workingdir' : Parameter(type=str,
                                 description='Working directory for command execution',
                                 default='.'),
    }

    outparameters = {
        'commandoutput' : Parameter(type=none_or(str),
                                    description='Command output (if captured)',
                                    default=None)
    }

    def run(self):
        cwd = os.getcwd()

        try:
            os.chdir(self.workingdir)
            self.commandoutput = systemCall(self.command,
                                            captureOutput=self.captureoutput,
                                            log=self.log)
        finally:
            os.chdir(cwd)




class Config(BuildStep):
    '''
    Build step to read given configuration file.
    '''
    parameters = {
        'path' : Parameter(type=str,
                                 description='Path to the configuration file',
                                 default='.'),
        'format' : Parameter(type=oneof('ini', 'py', 'auto'),
                     description='Format of config file',
                     default='auto'),
    }

    outparameters = {
        'config' : Parameter(type=dict,
                                    description='Command output (if captured)',
                                    default={})
    }

    def run(self):
        parseFuncs = {
            'ini' : self._parseIni,
            'py' : self._parsePy
        }

        self.log.info('Parse config: %s' % self.path)

        configFormat = self.format

        if configFormat == 'auto':
            configFormat = path.splitext(self.path)[1][1:]

            if configFormat not in parseFuncs.keys():
                raise RuntimeError('Unsupported configuration format: %s'
                                   % configFormat)

        self.log.debug('Used format: %s' % configFormat)


        self.config = parseFuncs[configFormat](self.path)

        self.log.debug('Parsed config: %r' % self.config)

    def _parseIni(self, path):
        cfg = {}

        parser = ConfigParser.SafeConfigParser()
        parser.readfp(open(path))

        for section in parser.sections():
            cfg[section] = {}

            for name, value in parser.items(section):
                cfg[section][name] = value

        return cfg


    def _parsePy(self, path):
        cfg = {}

        content = open(path).read()

        exec content in cfg
        del cfg['__builtins__']

        return cfg


class TmpDir(BuildStep):
    parameters = {
        'parentdir' : Parameter(type=str,
                                 description='Path to parent directory',
                                 default='/tmp'),
    }

    outparameters = {
        'tmpdir' : Parameter(type=str,
                                description='Created temporary directory',)
    }

    def run(self):
        timehash = hashlib.sha1(str(time.time())).hexdigest()
        dirhash = hashlib.sha1(self.parentdir).hexdigest()

        dest = hashlib.sha1(timehash + dirhash).hexdigest()
        dest = path.join(self.parentdir, dest)

        self.log.info('Create temporary dir: %s' % dest)

        ensureDirectory(dest)
        self.tmpdir = dest

    def cleanup(self):
        shutil.rmtree(self.tmpdir)



class RmPath(BuildStep):
    parameters = {
        'path' : Parameter(type=str,
                                 description='Path to remove'),
        'recursive' : Parameter(type=bool,
                                 description='Remove recursive',
                                 default=True),
    }

    def run(self):
        self.log.info('Remove path: %s' % self.path)

        if path.isfile(self.path):
            os.remove(self.path)
        elif path.isdir(self.path):
            if self.recursive:
                shutil.rmtree(self.path)
            else:
                os.rmdir(self.path)

        if path.exists(self.path):
            raise RuntimeError('Could not remove path')


class Partitioning(BuildStep):
    parameters = {
        'dev' : Parameter(type=str,
                                 description='Path to the device file'),
        'partitions' : Parameter(type=listof(int),
                                 description='List of partition sizes (in MB)')
    }

    def run(self):
        cmds = []

        for i in range(len(self.partitions)):
            cmds += self._createPartitionCmds(i+1, self.partitions[i])

        cmds.append('p') # print partition table
        cmds.append('w') # write partition table
        cmds.append('') # confirm

        shCmd = '(%s)' % ''.join([ 'echo %s;' % entry for entry in cmds])
        shCmd += '| fdisk %s 2>&1' % self.dev

        systemCall(shCmd, captureOutput=True, log=self.log)

    def _createPartitionCmds(self, index, size):
        cmds = [
            'n' # new partition
        ]

        if index < 4:
            cmds.append('p') # primary
        else:
            cmds.append('e') # extended

        cmds.append(str(index)) # partition number
        cmds.append('') # confirm

        cmds.append('+%dM' % size) # partition size

        return cmds

class DevMapper(BuildStep):
    '''
    This build step uses kpartx (devmapper) to map the partitions of the given
    device to own device files.
    '''
    parameters = {
        'dev' : Parameter(type=str,
                                 description='Path to the device file'),
    }

    outparameters = {
        'mapped' : Parameter(type=list,
                                description='Created device files',)
    }

    def run(self):
        # create device files
        systemCall('kpartx -v -a -s %s' % self.dev,
                   captureOutput=True,
                   log=self.log)

        # request a proper formated list of devs
        out = systemCall('kpartx -v -l -s %s' % self.dev,
                   captureOutput=True,
                   log=self.log)

        # store created device file paths
        self.mapped = []
        for line in out.splitlines():
            devFile = line.rpartition(':')[0].strip()
            self.mapped.append(path.join('/dev/mapper', devFile))

    def cleanup(self):
        systemCall('kpartx -v -d -s %s' % self.dev,
                   captureOutput=True,
                   log=self.log)

class CreateFileSystem(BuildStep):
    '''
    This build step creates the desired file system on the given device.
    Used tool: mkfs
    '''

    parameters = {
        'dev' : Parameter(type=str,
                                 description='Path to the device file'),
        'fstype' : Parameter(type=oneof('bfs',
                                        'cramfs',
                                        'ext2',
                                        'ext3',
                                        'ext4',
                                        'fat',
                                        'ntfs',
                                        'vfat'),
                                 description='Desired file system'),
    }

    def run(self):
        systemCall('mkfs -t %s %s' % (self.fstype, self.dev),
                   captureOutput=True,
                   log=self.log)


class Mount(BuildStep):
    '''
    This build step mounts given device to given mount point.
    '''
    parameters = {
        'dev' : Parameter(type=str,
                                 description='Path to the device file'),
        'mountpoint' : Parameter(type=str,
                                 description='Path to the mount point'),
    }

    def run(self):
        mount(self.dev, self.mountpoint, log=self.log)

    def cleanup(self):
        umount(self.mountpoint, log=self.log)


class MakeDirs(BuildStep):
    '''
    This build step create the desired directories.
    '''

    parameters = {
        'dirs' : Parameter(type=listof(str),
                                 description='List of directories'),
        'removeoncleanup' : Parameter(type=bool,
                                 description='Remove the directories on clenup',
                                 default=True),
    }

    def run(self):
        for entry in self.dirs:
            # TODO: Referencer support for nested types
            entry = Referencer(entry).evaluate(self.chain)
            self.log.debug('Create directory: %s ...' % entry)
            ensureDirectory(entry)

    def cleanup(self):
        if self.removeoncleanup:
            for entry in self.dirs:
                entry = Referencer(entry).evaluate(self.chain)
                shutil.rmtree(entry)


class Debootstrap(BuildStep):
    '''
    This build step bootstraps a basic debian system to the given directory.
    '''

    parameters = {
        'distribution' : Parameter(type=str,
                                 description='Desired distribution'),
        # TODO: map archs? => system analyzer?
        'arch' : Parameter(type=oneof('x86_64', 'i386', 'armel', 'armhf'),
                                 description='Desired architecture'),
        'destdir' : Parameter(type=str,
                                 description='Destination directory'),
    }

    def run(self):
        cmd = 'debootstrap --verbose --arch=%s ' % self.arch

        if self._isForeignArch():
            # separate first and second stage
            cmd += '--foreign '

        cmd += '%s %s' % (self.distribution, self.destdir)

        self.log.info('Bootstrapping ...')
        systemCall(cmd, captureOutput=True, log=self.log)

        if self._isForeignArch():
            self._strapSecondStage()

    def _isForeignArch(self):
        return self.arch != conduct.cfg['system']['arch']

    def _strapSecondStage(self):
        self.log.info('Boostrap second stage ...')
        qemuStatic = '/usr/bin/qemu-%s-static' % self.arch
        chrootQemuStaticPlace = path.join(self.destdir, 'usr', 'bin')

        shutil.copy(qemuStatic, chrootQemuStaticPlace)
        chrootedSystemCall(self.destdir,
                           'debootstrap/debootstrap --second-stage',
                           mountPseudoFs=False,
                           captureOutput=True,
                           log=self.log)











