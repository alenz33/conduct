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
This chain builds debian packages at the MLZ facility.
'''

parameters = {
    'pbuildercfgdir' : Parameter(type=str,
                            description='Config directory for pbuilder',
                            default='/etc/pbuilder'),
    'resultbasedir' : Parameter(type=str,
                            description='Base directory for the pbuilder result',
                            default='/var/cache/pbuilder'),
    'checkoutdir' : Parameter(type=str,
                            description='Directory for checking out projects',
                            default='/tmp'),
    'distribution' : Parameter(type=str,
                            description='Distribution to build for/in',
                            default='wheezy'),
    'gitbaseurl' : Parameter(type=str,
                            description='Base url to checkout projects',
                            default='ssh://alenz@forge.frm2.tum.de:29418/'),
    'gitcheckout' : Parameter(type=str,
                            description='Branch or tag to check out (last tag of not given)',
                            default=''),
    'arch' : Parameter(type=str,
                            description='Architecture to build for',
                            default='amd64'),
    'project' : Parameter(type=str,
                            description='Project (or pkg) to build',),
    'publish' : Parameter(type=bool,
                            description='Publish the resulting packages',
                            default=True),
    'local' : Parameter(type=bool,
                            description='Build without checkout (assume existing checkout)',
                            default=False),
}

# TODO: Map repo <-> pkg
# TODO: determine fitting pbuilder cfg
# TODO: checkout git if desired
# TODO: inject sources.list (hook?)
# TODO: apt-get update inside jail (hook?)
# TODO: build source package (may be not necessary when using pdebuild instead of pbuilder directly)
# TODO: build binary package
# TODO: publish package
# TODO: clean result files
# TODO: clean checkout if any
