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

import re
from os import path

from conduct.buildsteps.base import BuildStep
from conduct.util import systemCall
from conduct.param import Parameter, listof, referencer_or, Referencer

class Partitioning(BuildStep):
    parameters = {
        'dev' : Parameter(type=str,
                                 description='Path to the device file'),
        'partitions' : Parameter(type=listof(referencer_or(int)),
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

        systemCall(shCmd, log=self.log)

    def _createPartitionCmds(self, index, size):
        # TODO: better referencer handling: give step instead of chain
        if isinstance(size, Referencer):
            size = size.evaluate(self.chain, float)

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
                                description='Created device files',),
        'loopdev' : Parameter(type=str,
                                description='Used loop device',)
    }

    def run(self):
        # create device files
        systemCall('kpartx -v -a -s %s' % self.dev, log=self.log)

        # request a proper formated list of devs
        out = systemCall('kpartx -v -l -s %s' % self.dev, log=self.log)

        # store loop dev
        self.loopdev = re.findall('(/dev/.*?) ', out)[0]

        # store created device file paths
        self.mapped = []
        for line in out.splitlines():
            devFile = line.rpartition(':')[0].strip()
            self.mapped.append(path.join('/dev/mapper', devFile))

        self.log.info('Loop device: %s' % self.loopdev)
        self.log.info('Mapped devices: %s' % ', '.join(self.mapped))

    def cleanup(self):
        systemCall('kpartx -v -d -s %s' % self.dev,
                   log=self.log)