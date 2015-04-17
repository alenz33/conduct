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

import ConfigParser

from os import path

from conduct.buildsteps.base import BuildStep
from conduct.param import Parameter, oneof

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


class Calculation(BuildStep):
    '''
    Build step to do some calculation.
    '''
    parameters = {
        'formula' : Parameter(type=str,
                                 description='Formula to calculate',
                                 default='1'),
    }

    outparameters = {
        'result' : Parameter(type=float,
                                    description='Result of the calculation',
                                    default=1)
    }
    def run(self):
        self.result = float(eval(self.formula))

