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
#   Alexander Lenz <alexander.lenz@frm2.tum.de>
#
# *****************************************************************************

import logging
import subprocess

## Util funcs

def systemCall(cmd, sh=True, captureOutput=False, log=logging):
    log.debug('System call [sh:%s][captureOutput:%s]: %s' \
                  % (sh, captureOutput, cmd))

    if captureOutput:
        return subprocess.check_output(cmd, shell=sh)
    subprocess.check_call(cmd, shell=sh)


def dictToDataholder(d):
    class Dataholder(object):
        pass

    result = Dataholder()

    for key, value in d.iteritems():
        result.key = value

    return result