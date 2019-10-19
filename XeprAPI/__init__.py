# -*- coding: utf-8 -*-
#
# (c) Copyright 2014, Bruker BioSpin
#
# Modified by Sam Schott, University of Cambridge 2019.
#

import os
import sys

_msgprefix = "Xepr API: "
__version__ = "0.60"
__author__ = "Sam Schott, Bruker Biospin"

def _getpath(major, minor):
    toppath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(toppath, "%u.%u.x" % (major, minor))


def _main():
    major, minor = sys.version_info[:2]
    modpath = _getpath(major, minor)
    if not os.path.isdir(modpath):
        raise ImportError("%sNo support for Python V%u.%u.x (yet)" % _msgprefix)
    sys.path.insert(0, modpath)

_main()

from XeprAPImod import Xepr, DatasetError, DimensionError, ExperimentError, ParameterError, getXeprInstances
