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

def parseArgv(argv):
    parser = argparse.ArgumentParser(description='conduct - CONvenient Construction Tool',
                                     conflict_handler='resolve')

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
                        type=str,
                        help='Build chain',
                        required=True)

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

    # load and store global config
    conduct.cfg = config.loadConductConf(args.global_config)

    # configure logging
    initLogging(args.chain)


    try:
        BuildStep('s1', {}).build()
        BuildStep('s2', {}).build()
        BuildStep('s3', {}).build()
        bs = SystemCallStep('scs', {
            'command' : 'ls',
            'captureoutput' : True,
            'workingdir' : '/var/',
            })
        bs.build()
        print(bs.commandoutput)
        #bs = CopyBS('copysth', {})
        #bs.loglevel = 'debug'
        #bs.description = 'Some description'
        #bs.build()
    except Exception as e:
        conduct.log.exception(e)
        conduct.log.error('')
        conduct.log.error('Build failed')
        return 1



    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
