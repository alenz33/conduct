#!/usr/bin/env python
# *****************************************************************************
# conduct - CONvenient Construct Tool
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

import sys
import os
import logging
import argparse

def parseArgv(argv):
    parser = argparse.ArgumentParser(description='conduct - CONvenient Construct Tool',
                                     conflict_handler='resolve')

    parser.add_argument('-v', '--verbose', action='store_true',
        help='Verbose logging',
        default=False)

    return parser.parse_args(argv)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    # unbuffered output
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

    # parse cli args
    args = parseArgv(argv[1:])

    # configure logging
    logLevel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logLevel,
                    format='## [%(asctime)-15s][%(levelname)s]: %(message)s')

    return 0




if __name__ == '__main__':
    sys.exit(main(sys.argv))
