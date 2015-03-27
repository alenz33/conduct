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

import sys
import os
import logging
import argparse

import conduct

from conduct import loggers, config
from conduct.buildsteps import SystemCallStep, BuildStep
from conduct.chain import Chain
from conduct.util import loadChainFile, chainPathToName

def processGlobalArgs(parser, argv):
    parser.add_argument('-v',
                        '--verbose',
                        action='store_true',
                        help='Verbose logging',
                        default=False)

    parser.add_argument('-g',
                        '--global-config',
                        type=str,
                        help='Global config file (conduct.conf)',
                        default='/etc/conduct.conf')

    parser.add_argument('-c',
                        '--chain',
                        type=chainPathToName,
                        help='Desired chain',
                        required=True)

    parser.add_argument('-h',
                        '--help',
                        help='Print help',
                        action='store_true')

    # parse global args
    globalArgs, specArgs = parser.parse_known_args(argv)

    # init config
    # load and store global config
    conduct.cfg = config.loadConductConf(globalArgs.global_config)

    # handle help stuff
    if globalArgs.help and not specArgs:
        parser.print_help()
        print('')
        print('Available subcommands: build')
        parser.exit()

    return globalArgs

def addChainArgs(parser, chainName):
    chainDef = loadChainFile(chainName)

    for paramName, paramDef in chainDef['parameters'].iteritems():
        flag = '--%s' % paramName
        parser.add_argument(
            flag,
            type=paramDef.type,
            help=paramDef.description,
            required=(paramDef.default == None),
            default=paramDef.default
        )



def parseArgv(argv):
    parser = argparse.ArgumentParser(description='conduct - CONvenient Construction Tool',
                                     conflict_handler='resolve',
                                     add_help=False)

    globalArgs = processGlobalArgs(parser, argv)

    subparsers = parser.add_subparsers(title='actions',
                                       description='valid actions',
                                       dest='action')

    build = subparsers.add_parser('build', help='Build chain')

    # add chain specific params
    if globalArgs.chain:
        addChainArgs(build, globalArgs.chain)

    return parser.parse_args(argv)

def initLogging(logname, daemonize=False):
    globalcfg = conduct.cfg['conduct']

    conduct.log = logging.getLogger(logname)
    loglevel = loggers.LOGLEVELS[globalcfg['loglevel']]
    conduct.log.setLevel(loglevel)

    # console logging for fg process
    if not daemonize:
        conduct.log.addHandler(loggers.ColoredConsoleHandler())

    # logfile for fg and bg process
    conduct.log.addHandler(loggers.LogfileHandler(globalcfg['logdir'], logname))


def main(argv=None):
    if argv is None:
        argv = sys.argv

    # unbuffered output
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

    # parse cli args
    args = parseArgv(argv[1:])

    # configure logging
    initLogging(args.chain)

    chainDef = loadChainFile(args.chain)

    paramValues = {}
    for param in chainDef['parameters'].keys():
            paramValues[param] = getattr(args, param)


    chain = Chain(args.chain, paramValues)
    chain.build()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
