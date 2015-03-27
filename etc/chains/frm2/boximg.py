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
}

# Build steps
steps.imgdef   = Step('conduct.Config',
                        description='Read image definition file',
                        path='{chain.imgcfgdir}/{chain.imgname}.py')

steps.tmpdir   = Step('conduct.TmpDir',
                        description='Generate build dir',)

steps.imgfile   = Step('conduct.SystemCall',
                        description='Create empty image file',
                        command='dcfldd if=/dev/zero of={steps.tmpdir.tmpdir}/{chain.imgname}.img bs=1048576 count={steps.imgdef.config[size]}')

steps.partition   = Step('conduct.Partitioning',
                        description='Partition image file',
                        dev='{steps.tmpdir.tmpdir}/{chain.imgname}.img',
                        partitions=[3,5])

steps.cleanup   = Step('conduct.RmPath',
                        description='Cleanup tmp dir',
                        path='{steps.tmpdir.tmpdir}')


