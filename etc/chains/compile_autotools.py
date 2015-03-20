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

'''
Simple chain to compile software thats build is based on autotools.
'''

parameters = {
    'sourcedir' : Parameter(type=str,
                            description='Path to the source directory'),
}

steps = {
    'autogen' : BuildStep('conduct.SystemCallStep',
                          description='Generate configure via autogen.sh',
                          workingdir=params.sourcedir,
                          command='./autogen.sh',
    ),
    'configure' : BuildStep('conduct.SystemCallStep',
                          description='Execute configure script',
                          workingdir=params.sourcedir,
                          command='./configure',
    ),
    'make' : BuildStep('conduct.SystemCallStep',
                          description='Build software via make',
                          workingdir=params.sourcedir,
                          command='make',
    ),
}