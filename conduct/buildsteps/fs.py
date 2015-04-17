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
import time
import hashlib
import shutil

from os import path

from conduct.buildsteps.base import BuildStep
from conduct.util import systemCall, ensureDirectory, mount, umount
from conduct.param import Parameter, oneof, listof, Referencer


class WriteFile(BuildStep):
    parameters = {
        'path' : Parameter(type=str,
                                 description='Path to target file'),
        'content' : Parameter(type=str,
                                 description='Content wo write'),
        'append' : Parameter(type=bool,
                                 description='Append to the file '
                                    '(if existing)',
                                 default=False),
    }

    def run(self):
        ensureDirectory(path.dirname(self.path))

        openMode = 'a' if self.append else 'w'

        self.log.info('Write to file %s ...' % self.path)
        with open(self.path, openMode) as f:
            f.write(self.content)


class TmpDir(BuildStep):
    parameters = {
        'parentdir' : Parameter(type=str,
                                 description='Path to parent directory',
                                 default='/tmp'),
    }

    outparameters = {
        'tmpdir' : Parameter(type=str,
                                description='Created temporary directory',)
    }

    def run(self):
        timehash = hashlib.sha1(str(time.time())).hexdigest()
        dirhash = hashlib.sha1(self.parentdir).hexdigest()

        dest = hashlib.sha1(timehash + dirhash).hexdigest()
        dest = path.join(self.parentdir, dest)

        self.log.info('Create temporary dir: %s' % dest)

        ensureDirectory(dest)
        self.tmpdir = dest

    def cleanup(self):
        shutil.rmtree(self.tmpdir)



class RmPath(BuildStep):
    parameters = {
        'path' : Parameter(type=str,
                                 description='Path to remove'),
        'recursive' : Parameter(type=bool,
                                 description='Remove recursive',
                                 default=True),
    }

    def run(self):
        self.log.info('Remove path: %s' % self.path)

        if path.isfile(self.path):
            os.remove(self.path)
        elif path.isdir(self.path):
            if self.recursive:
                shutil.rmtree(self.path)
            else:
                os.rmdir(self.path)

        if path.exists(self.path):
            raise RuntimeError('Could not remove path')

class CreateFileSystem(BuildStep):
    '''
    This build step creates the desired file system on the given device.
    Used tool: mkfs
    '''

    parameters = {
        'dev' : Parameter(type=str,
                                 description='Path to the device file'),
        'fstype' : Parameter(type=oneof('bfs',
                                        'cramfs',
                                        'ext2',
                                        'ext3',
                                        'ext4',
                                        'fat',
                                        'ntfs',
                                        'vfat'),
                                 description='Desired file system'),
    }

    def run(self):
        systemCall('mkfs -t %s %s' % (self.fstype, self.dev), log=self.log)


class Mount(BuildStep):
    '''
    This build step mounts given device to given mount point.
    '''
    parameters = {
        'dev' : Parameter(type=str,
                                 description='Path to the device file'),
        'mountpoint' : Parameter(type=str,
                                 description='Path to the mount point'),
    }

    def run(self):
        mount(self.dev, self.mountpoint, log=self.log)

    def cleanup(self):
        umount(self.mountpoint, log=self.log)


class MakeDirs(BuildStep):
    '''
    This build step create the desired directories.
    '''

    parameters = {
        'dirs' : Parameter(type=listof(str),
                                 description='List of directories'),
        'removeoncleanup' : Parameter(type=bool,
                                 description='Remove the directories on clenup',
                                 default=True),
    }

    def run(self):
        for entry in self.dirs:
            # TODO: Referencer support for nested types
            entry = Referencer(entry).evaluate(self.chain)
            self.log.debug('Create directory: %s ...' % entry)
            ensureDirectory(entry)

    def cleanup(self):
        if self.removeoncleanup:
            for entry in self.dirs:
                entry = Referencer(entry).evaluate(self.chain)
                shutil.rmtree(entry)