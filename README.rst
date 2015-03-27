CONvenient Construction Tool
============================

`Documentation <http://conduct.rtfd.org>`_
Author: `Alexander Lenz <mailto:alexander.lenz@posteo.de>`_


conduct is a build system that is intended to be used as a standalone script (conduct.py) or in conjunction with some load balancer (e.g. via Jenkins).

The idea is to checkout/install conduct to some system, give it a build chain config and the necessary parameters, and everything else shall be done automatically. That means:

        Bootstrapping of necessary tools
        Configuring necessary tools
        Building by using the given chain config and parameters
        Cleanup after the build
        Rollback the boostrapped packages (if desired)

Basically, conduct’s goals are:

        easy to configure the build process
        easy to use the build process
        easy to extend for special needs
        consistent logging
        automatic boostrapping
        great selection of standard build steps




Special thanks for contribution and other input to:
	* `Georg Brandl <mailto:georg@python.org>`_
	* `Dr. Enrico Faulhaber <mailto:enrico.faulhaber@arcor.de>`_
