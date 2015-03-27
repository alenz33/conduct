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
Simple chain to compile software thats build is based on autotools.
'''

import conduct

# Short description which will be displayed on command line help.
description = 'Simple chain to compile software thats build is based on autotools'

# Chain specific parameters
parameters = {
    'sourcedir' : Parameter(type=str,
                            description='Path to the source directory'),
}

# Build steps
steps.autogen   = Step('conduct.SystemCall',
                        description='Generate configure via autogen.sh',
                        workingdir='{chain.sourcedir}',
                        command='./autogen.sh')
steps.configure = Step('conduct.SystemCall',
                        description='Execute configure script',
                        workingdir='{chain.sourcedir}',
                        command='./configure')
steps.make      = Step('conduct.SystemCall',
                        description='Build software via make',
                        workingdir='{chain.sourcedir}',
                        command='make')


