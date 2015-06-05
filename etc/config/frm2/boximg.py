import os.path

imgdir = '/share/ictrl/debuild/images'
archivedir = '/share/ictrl/debuild/images/archive'
archivesize = 5
loopdev = '/dev/loop%s'  # will be filled with the loop nr
part1dev = '/dev/mapper/loop%sp1'  # will be filled with the loop nr
part2dev = '/dev/mapper/loop%sp2'  # will be filled with the loop nr
tmpldir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
#imgcfgdir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'img'))
imgcfgdir = '/home/alenz/Projects/Gerrit/boxes/debuild/usr/local/debuild/imgsys/cfg/img/'
outdir = '/mnt/tmp'
builddir = '/mnt/tmp/imgbuild'
repreprobasedir = '/var/www/repos/apt/debian'
distribution = 'wheezy'
pkgmirror = 'deb [trusted=yes] http://172.25.2.104/repos/apt/debian wheezy main extra'

