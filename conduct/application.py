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

# TODO: Refactor q&d applications!!

import logging
import argparse
from ConfigParser import SafeConfigParser

from conduct import loggers
from conduct.chain import Chain
from conduct.util import getDefaultConfigPath, analyzeSystem, \
    loadChainDefinition, loadChainConfig, chainPathToName


class ConductApplication(object):
    def __init__(self):
        self._cfgFile = ''
        self._cfg = {}
        self._sysinfo = {}
        self._buildinfo = {}

    @property
    def cfg(self):
        return self._cfg

    @property
    def sysinfo(self):
        return self._sysinfo

    @property
    def buildinfo(self):
        return self._buildinfo

    def run(self, argv=[]):
        raise NotImplementedError('Abstract application cannot be used!')

    def build(self, chainName, paramOverrides= {}):
        self._analyzeSystem()

        self.log.info('Build chain: %s' % chainName)
        self._buildinfo['chain'] = chainName

        self.log.debug('Load chain default params ...')
        chainParams = loadChainConfig(chainName)

        self.log.debug('Apply param overrides ...')
        chainParams.update(paramOverrides)

        failed = False
        try:
            chain = Chain(chainName, chainParams)
            chain.build()
        except Exception as e:
            self.log.debug(e)
            failed = True

        self.log.info('')
        self.log.info('')
        self.log.info('='*80)
        self.log.info('')
        self.log.info('BUILD RESULT: %s' % 'FAILED' if failed else 'SUCCESS' )

        return failed

    def loadCfg(self, path):
        self._cfgFile = path

        parser = SafeConfigParser()
        parser.readfp(open(self._cfgFile))

        self._cfg = {
            option : value for option, value in parser.items('conduct')
        }

    def _analyzeSystem(self):
        if not self._sysinfo:
            self._sysinfo = analyzeSystem()

    def _initLogging(self):
        '''
        Initialize custom logging and configure it by global config.
        '''

        logging.setLoggerClass(loggers.ConductLogger)
        self.log = loggers.ConductLogger('conduct')
        loglevel = loggers.LOGLEVELS[self.cfg['loglevel']]
        self.log.setLevel(loglevel)

        # console logging for fg process
        self.log.addHandler(loggers.ColoredConsoleHandler())

        # logfile for fg and bg process
        self.log.addHandler(loggers.LogfileHandler(self.cfg['logdir'], 'conduct'))


class CliApplication(ConductApplication):
    def run(self, args):
        self._args = args
        self._parsedArgs = None
        self._globalArgs = None

        self._parser = argparse.ArgumentParser(
            description='conduct - CONvenient Construction Tool',
            conflict_handler='resolve',
            add_help=False)

        self._parseArgs()
        self._initLogging()

        # determine param overrides
        chainDef = loadChainDefinition(self._parsedArgs.chain)
        paramOverrides = {}
        for param in chainDef['parameters'].keys():
            val = getattr(self._parsedArgs, param)
            if val is not None:
                paramOverrides[param] = getattr(self._parsedArgs, param)


        # start actual build process
        return self.build(self._parsedArgs.chain, paramOverrides)

    def _parseArgs(self):
        '''
        Parse command line arguments.
        '''

        self._processGlobalArgs(self._args)
        self.loadCfg(self._globalArgs.global_config)

        subparsers = self._parser.add_subparsers(title='actions',
                                           description='valid actions',
                                           dest='action')

        build = subparsers.add_parser('build', help='Build chain')

        # add chain specific params
        if self._globalArgs.chain:
            self._addChainArgs(build, self._globalArgs.chain)

        self._parsedArgs = self._parser.parse_args(self._args)

    def _processGlobalArgs(self, argv):
        '''
        Parse 'global' arguments that does not belong to any chain.
        '''
        self._parser.add_argument('-g',
                            '--global-config',
                            type=str,
                            help='Global config file (conduct.conf)',
                            default=getDefaultConfigPath())

        self._parser.add_argument('-c',
                            '--chain',
                            type=chainPathToName,
                            help='Desired chain',
                            required=True)

        self._parser.add_argument('-h',
                            '--help',
                            help='Print help',
                            action='store_true')

        # parse global args
        self._globalArgs, specArgs = self._parser.parse_known_args(argv)

        # handle help stuff
        if self._globalArgs.help and not specArgs:
            self._parser.print_help()
            print('')
            print('Available subcommands: build')
            self._parser.exit()

    def _addChainArgs(self, subparser, chainName):
        '''
        Add parameters of given chain (by name) as arguments to the argparse self._parser.
        '''
        chainDef = loadChainDefinition(chainName)

        for paramName, paramDef in chainDef['parameters'].items():
            flag = '--%s' % paramName
            subparser.add_argument(
                flag,
                type=paramDef.type,
                help=paramDef.description,
                #required=(paramDef.default == None), # may be part of param file
            )






