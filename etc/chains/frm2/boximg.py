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

# Some specific global stuff

SOURCES_LIST = '''
deb http://ftp.de.debian.org/debian/ {chain.distribution} main
deb http://ftp.de.debian.org/debian/ {chain.distribution}-backports main
deb [trusted=yes] https://forge.frm2.tum.de/repos/apt/debian {chain.distribution} main extra
'''

GRUB_DEV_MAP = '''
(hd0)    {steps.devmap.loopdev}
(hd0,1)  {steps.devmap.mapped[0]}
'''

APT_PREF_BACKPORT = '''
Package: *
Pin: release a={chain.distribution}-backports
Pin-Priority: 500
'''

POLICY_RC_D = '''
#!/bin/sh
echo "All runlevel operations denied by policy" >&2
exit 101
'''

MOTD = '''
Welcome to one of the FRM-II TACO/TANGO boxes!

For more information about these boxes, contact the FRM-II
instrument control group (ictrl@frm2.tum.de).

Image information
=================
NAME:          {chain.imgname}
DISTRIBUTION:  {chain.distribution}
ARCH:          {steps.imgdef.config[ARCH]}

BUILD TIME:    {buildinfo.ctime}
BUILT ON:      {sysinfo.hostname}
'''

IMGFILE_TARGET = '{sysinfo.arch}.{chain.imgname}.' \
    '{buildinfo.localtime.tm_mday}_{buildinfo.localtime.tm_mon}_' \
    '{buildinfo.localtime.tm_year}'
IMGFILE_FULL = '{steps.tmpdir.tmpdir}/%s.full.img' % IMGFILE_TARGET
IMGFILE_PART = '{steps.tmpdir.tmpdir}/%s.part.img' % IMGFILE_TARGET


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
    'outdir' : Parameter(type=str,
                            description='Output directory for image files'),
    'builddir' : Parameter(type=str,
                            description='Build directory for image files',
                            default='/tmp'),
}

# Build steps
steps.imgdef   = Step('generic.Config',
                        description='Read image definition file',
                        path='{chain.imgcfgdir}/{chain.imgname}.py')

# -8: some space for mbr and stuff
steps.partsize   = Step('generic.Calculation',
                        description='Calculate partition size',
                        formula='({steps.imgdef.config[SIZE]} - 8) / 2')

steps.tmpdir   = Step('fs.TmpDir',
                        description='Generate build dir',
                        parentdir='{chain.builddir}')

steps.imgfile   = Step('syscall.SystemCall',
                        description='Create empty image file',
                        command='dcfldd if=/dev/zero '
                        'of=%s '
                        'bs=1048576 count={steps.imgdef.config[SIZE]}' % IMGFILE_FULL)

steps.partition   = Step('dev.Partitioning',
                        description='Partition image file',
                        dev=IMGFILE_FULL,
                        partitions=['{steps.partsize.result}','{steps.partsize.result}'])

steps.devmap   = Step('dev.DevMapper',
                        description='Map new image partitions to device files',
                        dev=IMGFILE_FULL)

steps.mkfs1   = Step('fs.CreateFileSystem',
                        description='Create ext2 file systems for first image partition',
                        dev='{steps.devmap.mapped[0]}',
                        fstype='ext2')

steps.mount   = Step('fs.Mount',
                        description='Mount first image partition',
                        dev='{steps.devmap.mapped[0]}',
                        mountpoint='{steps.tmpdir.tmpdir}/mount')

steps.mkchrootdirs   = Step('fs.MakeDirs',
                        description='Create some necessary dirs for the chroot environment',
                        removeoncleanup=False,
                        dirs=[
                            '{steps.mount.mountpoint}/boot/grub',
                            ])

steps.debootstrap   = Step('deb.Debootstrap',
                        description='Boostrap basic system',
                        distribution='{chain.distribution}',
                        arch='{steps.imgdef.config[ARCH]}',
                        destdir='{steps.tmpdir.tmpdir}/mount',
                        includes=['apt-transport-https', 'ca-certificates'])

steps.srclst   = Step('fs.WriteFile',
                        description='Create source list',
                        path='{steps.mount.mountpoint}/etc/apt/sources.list',
                        append=True,
                        content=SOURCES_LIST)

steps.aptupdate   = Step('syscall.ChrootedSystemCall',
                        description='Update package lists',
                        command='apt-get update',
                        chrootdir='{steps.mount.mountpoint}')

steps.kernel   = Step('deb.InstallDebPkg',
                        description='Install kernel image',
                        pkg='linux-image-{steps.imgdef.config[KERNEL]}',
                        chrootdir='{steps.mount.mountpoint}')

steps.grub   = Step('deb.InstallDebPkg',
                        description='Install bootloader (grub2)',
                        pkg='grub2',
                        chrootdir='{steps.mount.mountpoint}')

steps.grubdevmap   = Step('fs.WriteFile',
                        description='Create source list',
                        path='{steps.mount.mountpoint}/boot/device.map',
                        content=GRUB_DEV_MAP)

steps.mbr   = Step('syscall.SystemCall',
                        description='Install grub2 to mbr',
                        command='grub-install --no-floppy --grub-mkdevicemap='
                            '{steps.mount.mountpoint}/boot/device.map '
                            '--root-directory={steps.mount.mountpoint} '
                            '{steps.devmap.loopdev}')

steps.pinbp   = Step('fs.WriteFile',
                        description='Pin backports to normal level',
                        path='{steps.mount.mountpoint}/etc/apt/preferences.d/backports',
                        content=APT_PREF_BACKPORT)

## INSERT HERE: old workaround: install taco first may be possible

steps.policy   = Step('fs.WriteFile',
                        description='Forbid execution of init scripts on installation',
                        path='{steps.mount.mountpoint}/usr/sbin/policy-rc.d',
                        content=POLICY_RC_D)

steps.policyperm   = Step('syscall.ChrootedSystemCall',
                        description='Enable policy-rc.d',
                        command='chmod +x /usr/sbin/policy-rc.d',
                        chrootdir='{steps.mount.mountpoint}')

steps.pkgbasedeps   = Step('deb.InstallDebPkg',
                        description='Install base img pkg)',
                        pkg='boxes-base',
                        chrootdir='{steps.mount.mountpoint}',
                        depsonly=True)

steps.pkgplatformdeps   = Step('deb.InstallDebPkg',
                        description='Install platform img pkg)',
                        pkg='boxes-{steps.imgdef.config[PLATFORM]}',
                        chrootdir='{steps.mount.mountpoint}',
                        depsonly=True)

steps.pkgimgdeps   = Step('deb.InstallDebPkg',
                        description='Install specific img pkg)',
                        pkg='boxes-{chain.imgname}',
                        chrootdir='{steps.mount.mountpoint}',
                        depsonly=True)

steps.pkgbase   = Step('deb.InstallDebPkg',
                        description='Install base img pkg)',
                        pkg='boxes-base',
                        chrootdir='{steps.mount.mountpoint}')

steps.pkgplatform   = Step('deb.InstallDebPkg',
                        description='Install platform img pkg)',
                        pkg='boxes-{steps.imgdef.config[PLATFORM]}',
                        chrootdir='{steps.mount.mountpoint}')

steps.pkgimg   = Step('deb.InstallDebPkg',
                        description='Install specific img pkg)',
                        pkg='boxes-{chain.imgname}',
                        chrootdir='{steps.mount.mountpoint}')

steps.delpolicy   = Step('fs.RmPath',
                        description='Reenable init.d invokation',
                        path='{steps.mount.mountpoint}/usr/sbin/policy-rc.d')

steps.namevmlinuz   = Step('fs.MovePath',
                        description='Rename kernel image to unspecific name',
                        source='{steps.mount.mountpoint}/boot/vmlinuz*',
                        destination='{steps.mount.mountpoint}/boot/vmlinuz')

steps.nameinitrd   = Step('fs.MovePath',
                        description='Rename init ramdisk to unspecific name',
                        source='{steps.mount.mountpoint}/boot/initrd.img*',
                        destination='{steps.mount.mountpoint}/boot/vmlinuz')

# TODO: copy shadow file (argh pseudo security)
# TODO: copy ssh files (argh pseudo security)

steps.defaultsh   = Step('syscall.ChrootedSystemCall',
                        description='Use zsh as default shell',
                        command='chsh -s /usr/bin/zsh root',
                        chrootdir='{steps.mount.mountpoint}')

# TODO: generate taco_log.cfg

steps.genicse   = Step('syscall.ChrootedSystemCall',
                        description='Generate generic icse conf',
                        command='/etc/init.d/genicseconf',
                        chrootdir='{steps.mount.mountpoint}')

steps.cleantaco   = Step('fs.RmPath',
                        description='Remove superfluent taco stuff',
                        path='{steps.mount.mountpoint}/opt/taco/share/taco/dbase/res/TEST')

steps.disdynmotd   = Step('syscall.ChrootedSystemCall',
                        description='Disable dynamic motd generation',
                        command='update-rc.d motd remove',
                        chrootdir='{steps.mount.mountpoint}')

# TODO: create proper motd with all neccessary info (build time etc)
steps.motd   = Step('fs.WriteFile',
                        description='Create motd',
                        path='{steps.mount.mountpoint}/etc/motd',
                        append=True,
                        content=MOTD)

steps.umount   = Step('generic.TriggerCleanup',
                        description='Unmount first image partition',
                        step='mount')

steps.duppart   = Step('syscall.SystemCall',
                        description='Dupilcate root partition',
                        command='dcfldd if={steps.devmap.mapped[0]} of={steps.devmap.mapped[1]}')

steps.mount2   = Step('fs.Mount',
                        description='Mount second image partition',
                        dev='{steps.devmap.mapped[1]}',
                        mountpoint='{steps.tmpdir.tmpdir}/mount2')

steps.fixfstab   = Step('syscall.ChrootedSystemCall',
                        description='Fix fstab on second partition',
                        command='sed -i -e "s/sda1/sda2/g" /etc/fstab',
                        chrootdir='{steps.mount2.mountpoint}')

steps.umount2   = Step('generic.TriggerCleanup',
                        description='Unmount second image partition',
                        step='mount2')

steps.partimg   = Step('syscall.SystemCall',
                        description='Create part img file',
                        command='dcfldd if={steps.devmap.mapped[0]} of=%s' % IMGFILE_PART)

steps.unmap   = Step('generic.TriggerCleanup',
                        description='Unmap devices',
                        step='devmap')

steps.mvtooutdir   = Step('fs.MovePath',
                        description='Move image files to output dir',
                        source='{steps.tmpdir.tmpdir}/%s.*.img' % IMGFILE_TARGET,
                        destination='{chain.outdir}')

