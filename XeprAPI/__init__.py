# -*- coding: utf-8 -*-
#
# (c) Copyright 2014, Bruker BioSpin
#
# Modified by Sam Schott, University of Cambridge 2019.
#

from .main import (
    Xepr, getXeprInstances,
    DatasetError, DimensionError, ExperimentError, ParameterError,
)


_msgprefix = "Xepr API: "
__version__ = "0.61-dev"
__author__ = "Sam Schott, Bruker Biospin"
