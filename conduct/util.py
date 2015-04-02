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

import os
import logging
import platform
import select
import time


from collections import OrderedDict
from ConfigParser import SafeConfigParser
from os import path
from subprocess import Popen, PIPE, CalledProcessError

import conduct
from conduct.param import Parameter

## Utils classes

class Referencer(object):
    def __init__(self, fmt):
        self.fmt = fmt

    def evaluate(self, chain):
        result = self.fmt.format(chain=Dataholder(chain.params),
                            steps=Dataholder(chain.steps))

        return result

    def resolve(self, adr, chain):
        parts = adr.split('.')
        # chain.parameter
        # or
        # steps.stepname.parameter

        if parts[0] == 'chain':
            return chain.params[parts[1]]
        elif parts[0] == 'steps':
            step = chain.steps[parts[1]]
            return getattr(step, parts[2])

        raise RuntimeError('Could not resolve reference: %s' % adr)

class AttrStringifier(object):
    def __getattr__(self, name):
        return name

# TODO: Better name
class ObjectiveOrderedDict(object):
    def __init__(self):
        self.entries = OrderedDict()

    def __setattr__(self, name, value):
        if name == 'entries':
            return object.__setattr__(self, name, value)
        self.entries[name] = value


class Dataholder(object):
    def __init__(self, modelDict):
        self._modelDict = modelDict

    def __getattr__(self, name):
        if name in self._modelDict:
            return self._modelDict[name]


## Util funcs

def analyzeSystem():
    conduct.log.info('Analyze current system ...')

    # basic information
    info = platform.uname()
    infoKeys = ('os',
                'hostname',
                'release',
                'version',
                'arch',
                'processor')

    info = OrderedDict(zip(infoKeys, info))

    # detailed arch info
    info.update(zip(('bits', 'binformat'), platform.architecture()))


    for key, value in info.items():
        conduct.log.debug('{:<10}: {}'.format(key, value))

    return info


def loadConductConf(cfgPath=None):
    if cfgPath is None:
        cfgPath = getDefaultConfigPath()

    parser = SafeConfigParser()
    parser.readfp(open(cfgPath))

    cfg = {'conduct' : {
        option : value for option, value in parser.items('conduct')
    }}

    return cfg

def getDefaultConfigPath():
    inplacePath = path.join(path.dirname(__file__),
                                '..',
                                'etc',
                                'conduct.conf')
    if path.isfile(inplacePath):
        return inplacePath
    return '/etc/entangle.conf'


def logMultipleLines(strOrList, logFunc=None):
    if logFunc is None:
        logFunc = conduct.log.info

    if isinstance(strOrList, str):
        strOrList = strOrList.splitlines()

    for line in strOrList:
        logFunc(line)

def mount(dev, mountpoint, flags='', log=None):
        ensureDirectory(mountpoint)
        systemCall('mount %s %s %s' % (flags, dev, mountpoint),
                   log=log)

def umount(mountpoint, log=None):
    systemCall('umount %s' % mountpoint,
               log=log)

def systemCall(cmd, sh=True, log=None):
    if log is None:
        log = conduct.log

    log.debug('System call [sh:%s]: %s' \
              % (sh, cmd))

    out = []
    proc = None
    poller = None

    def pollOutput():
        '''
        Read, log and store output (if any) from processes pipes.
        '''
         # collect fds with new output
        fds = [entry[0] for entry in poller.poll()]

        if proc.stdout.fileno() in fds:
            for line in iter(proc.stdout.readline, ''):
                log.debug(line.strip())
                out.append(line)
        if proc.stderr.fileno() in fds:
            for line in iter(proc.stderr.readline, ''):
                log.warning(line.strip())


    while True:
        if proc is None:
            # create and start process
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=sh)

            # create poll select
            poller = select.poll()

            # register pipes to polling
            poller.register(proc.stdout, select.POLLIN)
            poller.register(proc.stderr, select.POLLIN)

        pollOutput()

        if proc.poll() is not None: # proc finished
            break

    # poll once after the process ended to collect all the missing output
    pollOutput()

    # check return code
    if proc.returncode != 0:
        raise CalledProcessError(proc.returncode, cmd, ''.join(out))

    return ''.join(out)

def chrootedSystemCall(chrootDir, cmd, sh=True, mountPseudoFs=True, log=None):
    if log is None:
        log = conduct.log

    # determine mount points for pseudo fs
    proc = path.join(chrootDir, 'proc')
    sys = path.join(chrootDir, 'sys')
    dev = path.join(chrootDir, 'dev')
    devpts = path.join(chrootDir, 'dev', 'pts')

    # mount pseudo fs
    if mountPseudoFs:
        mount('proc', proc, '-t proc')
        mount('/sys', sys, '--rbind')
        mount('/dev', dev, '--rbind')

    try:
        # exec chrooted cmd
        self.log.debug('Execute chrooted command ...')
        cmd = 'chroot %s %s' % (chrootDir, cmd)
        return systemCall(cmd, sh, log)
    finally:
        # umount if pseudo fs was mounted
        if mountPseudoFs:
            # handle devpts
            if path.exists(devpts):
                umount(devpts)
            umount(dev)
            umount(sys)
            umount(proc)



def dictToDataholder(d):
    class Dataholder(object):
        pass

    result = Dataholder()

    for key, value in d.items():
        result.key = value

    return result

def chainPathToName(path):
    return path.replace(os.sep, ':')

def chainNameToPath(name):
    return name.replace(':', os.sep)

def loadPyFile(path, ns=None):
    if ns is None:
        ns = {}

    ns['__file__'] = path

    exec open(path).read() in ns

    del ns['__builtins__']

    return ns

def loadChainDefinition(chainName):
    # caching
    if 'chains' not in conduct.cfg:
        conduct.cfg['chains'] = {}

    if chainName in conduct.cfg['chains']:
        return conduct.cfg['chains'][chainName]


    # determine chain file location
    chainDir = conduct.cfg['conduct']['chaindefdir']
    chainFile = path.join(chainDir, '%s.py' % chainNameToPath(chainName))

    if not path.exists(chainFile):
        raise IOError('Chain file for \'%s\' not found (Should be: %s)'
                      % (chainName, chainFile))

    # prepare exection namespace
    ns = {
        'Parameter' : Parameter,
        'Step' : lambda cls, **params: ('step:%s' % cls, params),
        'Chain' : lambda cls, **params: ('chain:%s' % cls, params),
        'steps' : ObjectiveOrderedDict(),
    }

    # execute and extract all the interesting data
    ns = loadPyFile(chainFile, ns)

    chainDef = {}

    for entry in ['description', 'parameters']:
        chainDef[entry] = ns[entry]

    chainDef['steps'] = ns['steps'].entries

    # cache
    conduct.cfg['chains'][chainName] = chainDef

    return chainDef

def loadChainConfig(chainName):
    # determine chain file location
    cfgDir = conduct.cfg['conduct']['chaincfgdir']
    cfgFile = path.join(cfgDir, '%s.py' % chainNameToPath(chainName))

    if path.exists(cfgFile):
        return loadPyFile(cfgFile)
    return {}

def ensureDirectory(dirpath):
    if not path.isdir(dirpath):
        os.makedirs(dirpath)


