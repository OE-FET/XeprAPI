# -*- coding: utf-8 -*-

#
# findXeprAPI.py         (c) Copyright 2013, Bruker BioSpin
#
# This script helps finding the actual XeprAPI module. If imported *prior* to XeprAPI,
# it is going to look for the module in the standard locations and will set the search
# path appropriately. If the PYTHONPATH environment variable is set it is taken into
# account first; thus, by setting the PYTHONPATH appropriately, the standard search
# order can can be overridden.
#


import os,sys,imp


try:
    if "XEPR_SHARED_DIR" in os.environ:
        raise ImportError   # force search if python is called from Xepr
    else:
        # do we find the module already now? That is, is it accessible by way of PYTHONPATH?
        imp.find_module("XeprAPI")
        print >>sys.stderr, "Found XeprAPI module (did not have to search for it)."
except:  # not found using current list of paths
    sys.path.insert(0, os.popen("Xepr --apipath").read())  # this locates the XeprAPI module
