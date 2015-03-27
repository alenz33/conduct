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
import subprocess

from collections import OrderedDict
from os import path

import conduct
from conduct.param import Parameter

## Utils classes

class Referencer(object):
    def __init__(self, adr):
        self.adr = adr

    def resolve(self, chain):
        parts = self.adr.split('.')
        # chain.parameter
        # or
        # steps.stepname.parameter

        if parts[0] == 'chain':
            return chain.params[parts[1]]
        elif parts[0] == 'steps':
            step = chain.steps[parts[1]]
            return getattr(step, parts[2])

        raise RuntimeError('Could not resolve reference: %s' % self.adr)

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


## Util funcs

def systemCall(cmd, sh=True, captureOutput=False, log=None):
    if log is not None:
        log.debug('System call [sh:%s][captureOutput:%s]: %s' \
                  % (sh, captureOutput, cmd))

    if captureOutput:
        return subprocess.check_output(cmd, shell=sh)
    subprocess.check_call(cmd, shell=sh)


def dictToDataholder(d):
    class Dataholder(object):
        pass

    result = Dataholder()

    for key, value in d.iteritems():
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
        'ref' : lambda refAdr: Referencer(refAdr),
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

