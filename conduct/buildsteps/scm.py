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

import shutil

from conduct.buildsteps.base import BuildStep
from conduct.param import Parameter
from conduct.util import systemCall


class GitClone(BuildStep):
    '''
    Clones a git project.
    '''
    parameters = {
        'url' : Parameter(type=str,
                                 description='Url to clone from'),
        'destdir' : Parameter(type=str,
                                 description='Destination directory to clone '
                                 'to (will be completely removed during '
                                 'cleanup!'),
        'target' : Parameter(type=str,
                                 description='Checkout target (tag or branch)',
                                 default=''),
        'asbranch' : Parameter(type=str,
                                 description='Checkout the desired target as '
                                 'given branch',
                                 default=''),
    }

    def run(self):
        systemCall('git clone %s %s' % (self.url, self.destdir))

        if self.target:
            checkoutCmd = 'git --git-dir=%s/.git --work-tree=%s checkout %s' % (
                self.destdir, self.destdir, self.target
                )

            if self.asbranch:
                checkoutCmd += ' -b %s' % self.asbranch

            systemCall(checkoutCmd)

    def cleanup(self):
        shutil.rmtree(self.destdir)
