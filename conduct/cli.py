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

import argparse

import conduct
from conduct.util import chainPathToName, loadConductConf, loadChainDefinition


def processGlobalArgs(parser, argv):
    '''
    Parse 'global' arguments that does not belong to any chain.
    '''
    parser.add_argument('-g',
                        '--global-config',
                        type=str,
                        help='Global config file (conduct.conf)',)

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
    conduct.cfg = loadConductConf(globalArgs.global_config)

    # handle help stuff
    if globalArgs.help and not specArgs:
        parser.print_help()
        print('')
        print('Available subcommands: build')
        parser.exit()

    return globalArgs

def addChainArgs(parser, chainName):
    '''
    Add parameters of given chain (by name) as arguments to the argparse parser.
    '''
    chainDef = loadChainDefinition(chainName)

    for paramName, paramDef in chainDef['parameters'].items():
        flag = '--%s' % paramName
        parser.add_argument(
            flag,
            type=paramDef.type,
            help=paramDef.description,
            #required=(paramDef.default == None), # may be part of param file
        )



def parseArgv(argv):
    '''
    Parse command line arguments.
    '''
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
