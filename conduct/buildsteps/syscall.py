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

from conduct.buildsteps.base import BuildStep
from conduct.util import systemCall, chrootedSystemCall
from conduct.param import Parameter, none_or

class SystemCall(BuildStep):
    '''
    Build step to execute given shell command.
    '''
    parameters = {
        'command' : Parameter(type=str,
                              description='command to execute'),
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
            self.commandoutput = systemCall(self.command, log=self.log)
        finally:
            os.chdir(cwd)

class ChrootedSystemCall(BuildStep):
    '''
    Build step to execute given shell command in a chroot environment.
    '''
    parameters = {
        'command' : Parameter(type=str,
                              description='command to execute'),
        'chrootdir' : Parameter(type=str,
                                 description='Chroot directory',
                                 default='.'),
    }

    outparameters = {
        'commandoutput' : Parameter(type=none_or(str),
                                    description='Command output (if captured)',
                                    default=None)
    }

    def run(self):
        self.commandoutput = chrootedSystemCall(self.chrootdir,
                                                self.command,
                                                log=self.log)