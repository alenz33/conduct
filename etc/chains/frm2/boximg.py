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

# Docstring for full documentation of chain
'''
This chain builds the image of FRM II's TACO/TANGO boxes.
'''

# Short description which will be displayed on command line help.
description = 'This chain builds the image of FRM II\'s TACO/TANGO boxes.'

# Chain specific parameters
parameters = {
    'imgname' : Parameter(type=str,
                            description='Image name'),
    'imgcfgdir' : Parameter(type=str,
                            description='Image config directory'),
    'distribution' : Parameter(type=str,
                            description='Distribution to boostrap onto the image'),
}

# Build steps
steps.imgdef   = Step('conduct.Config',
                        description='Read image definition file',
                        path='{chain.imgcfgdir}/{chain.imgname}.py',
                        retries=1)

steps.tmpdir   = Step('conduct.TmpDir',
                        description='Generate build dir',)

steps.imgfile   = Step('conduct.SystemCall',
                        description='Create empty image file',
                        command='dcfldd if=/dev/zero '
                        'of={steps.tmpdir.tmpdir}/{chain.imgname}.img '
                        'bs=1048576 count={steps.imgdef.config[size]}')

steps.partition   = Step('conduct.Partitioning',
                        description='Partition image file',
                        dev='{steps.tmpdir.tmpdir}/{chain.imgname}.img',
                        partitions=[1020,1020])

steps.devmap   = Step('conduct.DevMapper',
                        description='Map new image partitions to device files',
                        dev='{steps.tmpdir.tmpdir}/{chain.imgname}.img')

steps.mkfs1   = Step('conduct.CreateFileSystem',
                        description='Create ext2 file systems for first image partition',
                        dev='{steps.devmap.mapped[0]}',
                        fstype='ext2')

steps.mount   = Step('conduct.Mount',
                        description='Mount first image partition',
                        dev='{steps.devmap.mapped[0]}',
                        mountpoint='{steps.tmpdir.tmpdir}/mount')

steps.mkchrootdirs   = Step('conduct.MakeDirs',
                        description='Create some necessary dirs for the chroot environment',
                        dirs=[
                            '{steps.mount.mountpoint}/boot/grub',
                            ])

steps.debootstrap   = Step('conduct.Debootstrap',
                        description='Boostrap basic system',
                        distribution='{chain.distribution}',
                        arch='i386',
                        destdir='{steps.tmpdir.tmpdir}/mount')

# replace by cp + sed steps
steps.aptmain   = Step('conduct.SystemCall',
                        description='Add main apt repo',
                        command='echo "deb http://ftp.de.debian.org/debian/ '
                        '{chain.distribution} main" >> '
                        '{steps.mount.mountpoint}/etc/apt/sources.list')

# replace by cp + sed steps
steps.aptbackp   = Step('conduct.SystemCall',
                        description='Add backport apt repo',
                        command='echo "deb http://ftp.de.debian.org/debian/ '
                        '{chain.distribution}-backports main" >> '
                        '{steps.mount.mountpoint}/etc/apt/sources.list')

steps.aptupdate   = Step('conduct.ChrootedSystemCall',
                        description='Update package lists',
                        command='apt-get update',
                        chrootdir='{steps.mount.mountpoint}')


