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

from os import path

import conduct

from conduct.buildsteps.base import BuildStep
from conduct.util import systemCall, chrootedSystemCall
from conduct.param import Parameter, oneof

class Debootstrap(BuildStep):
    '''
    This build step bootstraps a basic debian system to the given directory.
    '''

    parameters = {
        'distribution' : Parameter(type=str,
                                 description='Desired distribution'),
        # TODO: map archs? => system analyzer?
        'arch' : Parameter(type=str,
                                 description='Desired architecture'),
        'destdir' : Parameter(type=str,
                                 description='Destination directory'),
    }

    def run(self):
        cmd = 'debootstrap --verbose --arch=%s ' % self.arch

        if self._isForeignArch():
            # separate first and second stage
            cmd += '--foreign '

        cmd += '%s %s' % (self.distribution, self.destdir)

        self.log.info('Bootstrapping ...')
        systemCall(cmd, log=self.log)

        if self._isForeignArch():
            self._strapSecondStage()

    def _isForeignArch(self):
        return self.arch != conduct.cfg['system']['arch']

    def _strapSecondStage(self):
        self.log.info('Boostrap second stage ...')
        qemuStatic = '/usr/bin/qemu-%s-static' % self.arch
        chrootQemuStaticPlace = path.join(self.destdir, 'usr', 'bin')

        self.log.debug('Copy qemu static to chroot ...')
        shutil.copy(qemuStatic, chrootQemuStaticPlace)
        chrootedSystemCall(self.destdir,
                           'debootstrap/debootstrap --second-stage',
                           mountPseudoFs=False,
                           log=self.log)

class InstallDebPkg(BuildStep):
    parameters = {
        'pkg' : Parameter(type=str,
                                 description='Package to install'),
        'chrootdir' : Parameter(type=str,
                                 description='Chroot directory (if desired)',
                                 default=''),
    }

    def run(self):
        cmd = 'env DEBIAN_FRONTEND=noninteractive ' \
                'apt-get install --yes --force-yes ' \
                '--no-install-recommends ' \
                '-o Dpkg::Options::="--force-overwrite" ' \
                '-o Dpkg::Options::="--force-confnew" ' \
                '%s' % self.pkg

        if self.chrootdir:
            chrootedSystemCall(self.chrootdir, cmd, log=self.log)
        else:
            systemCall(cmd, log=self.log)

