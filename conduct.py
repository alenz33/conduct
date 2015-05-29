#!/usr/bin/env python
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

'''
conduct's main script.
Handles all command line arguments, creates and executes the given chain.
'''

import sys
import os
import argparse

import conduct

from conduct import loggers
from conduct.chain import Chain
from conduct.cli import parseArgv
from conduct.util import loadChainDefinition, loadChainConfig, analyzeSystem


def initLogging(daemonize=False):
    '''
    Initialize custom logging and configure it by global config.
    '''
    globalcfg = conduct.cfg['conduct']

    conduct.log = loggers.ConductLogger('conduct')
    loglevel = loggers.LOGLEVELS[globalcfg['loglevel']]
    conduct.log.setLevel(loglevel)

    # console logging for fg process
    if not daemonize:
        conduct.log.addHandler(loggers.ColoredConsoleHandler())

    # logfile for fg and bg process
    conduct.log.addHandler(loggers.LogfileHandler(globalcfg['logdir'], 'conduct'))


def main(argv=None):
    if argv is None:
        argv = sys.argv

    # unbuffered output
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

    # parse cli args
    args = parseArgv(argv[1:])

    # configure logging
    initLogging()

    # collect some system information
    conduct.cfg['system'] = analyzeSystem()

    chainDef = loadChainDefinition(args.chain)

    # load chain config if any
    paramValues = loadChainConfig(args.chain)

    # override/apply cli params
    for param in chainDef['parameters'].keys():
        val = getattr(args, param)
        if val is not None:
            paramValues[param] = getattr(args, param)


    conduct.log.info('Build chain: %s' % args.chain)

    failed = False
    try:
        chain = Chain(args.chain, paramValues)
        chain.build()
    except Exception as e:
        conduct.log.debug(e)
        failed = True

    conduct.log.info('')
    conduct.log.info('')
    conduct.log.info('================================================================================')
    conduct.log.info('')
    conduct.log.info('BUILD RESULT: %s' % 'FAILED' if failed else 'SUCCESS' )

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
