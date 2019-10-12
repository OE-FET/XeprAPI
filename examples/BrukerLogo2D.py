# -*- coding: utf-8 -*-
    #NOWAIT#    do not wait for a key to be pressed when the script is finished.
#
# BrukerLogo2D.py          (c) Copyright 2012, Bruker BioSpin
#
# This script demonstrates how to
#       - construct 2D datasets from external data
#       - use native Xepr commands by way of Xepr API
#
#
# Note: Prior to running any Xepr API scripts, the Xepr API has to be
#       enabled once in Xepr by selecting the menu item "Enable Xepr API"
#       from the "XeprAPI" sub-menu of the "Processing" menu. However,
#       if the script is run from within Xepr (menu item "Run XeprAPI Script"),
#       the API will be enabled automatically.
#


import os,sys; sys.path.insert(0, os.popen("Xepr --apipath").read())  # this locates the XeprAPI module

import XeprAPI          # load the Xepr API module



#------------------ the following stuff is not related to Xepr -------------------------------


# some 2D data to be loaded into Xepr as a 2D dataset
LOGOURL="http://www.bruker.com/typo3conf/ext/pt_campo/Resources/Public/Images/bruker_logo.png"	# use Bruker logo as the "data"
XPIXELS=1024	# minimum number of pixels on x axis


try:
    import urllib2				# third-party library to fetch data from the internet
    import Image				# module for image processing
except:                         # if we could not load the modules, just ignore them
    pass
from StringIO import StringIO		# Python module for IO via string stream
import numpy as NP			# powerful array module for Python


try:					# try to fetch the data from the internet
    logodata=urllib2.urlopen(LOGOURL).read()
    logo=Image.open(StringIO(logodata))
    xdim,ydim = logo.size
    if xdim < XPIXELS:  # stretch image accordingly		# now stretch the image to a proper size
        ydim=ydim*XPIXELS/xdim; xdim=XPIXELS
        logo=logo.resize((xdim, ydim), Image.BICUBIC)		# using bicubic interpolation
        logo=logo.convert(mode="L", colors=256)
        xdim,ydim = logo.size
except:					# show error if we were not successful
    print "Could not load/process image at %s,\nusing image file instead." % LOGOURL
    logo = None
    scriptpath = os.path.dirname(os.path.realpath(sys.argv[0]))  # get location of script
    ord_array = NP.load(scriptpath + "/bruker_logo.npy").astype(int)
    ydim,xdim = ord_array.shape



#------------------------------- Xepr related stuff below this line ---------------------------


  
Xepr=XeprAPI.Xepr()  			# now we are ready to actually talk to Xepr using the API


Xepr.XeprCmds.vpClear()         # clear the viewport using an Xepr command
  
  
print "Processing 2D dataset...takes a few seconds..."


dset = Xepr.XeprDataset(size=(xdim, ydim))          # create a properly shaped 2D dataset
                                                    # corresponding to the primary dataset of Xepr

dset.X = xrange(xdim)                               # set the X abscissa values of the dataset
dset.Y = xrange(ydim)                               # same for the Y abscissa

# this transforms the image into an array of gray scale values
if logo != None:
    ord_array = NP.fromiter(logo.getdata(), dtype=int).reshape(ydim,xdim)[::-1]

dset.O = ord_array                                  # now set the 2D ordinate data of the dataset

dset.update(refresh = True)                         # transfer the dataset to Xepr's primary dataset
                                                    # and refresh the GUI to display it

# set up 2D mode and b&w view for the viewport
Xepr.XeprCmds.vpCvtViewp(-1)
try:        # try to set color scheme
    Xepr.XeprCmds.vp2DColorScheme("Current", "b&w")      # set color scheme using native Xepr command
except:     # did not work, need to transform 1D viewport to 2D first
    Xepr.XeprCmds.vpCvtViewp(-1)    # 1D  <-->  2D  using native Xepr command
    Xepr.XeprCmds.vp2DColorScheme("Current", "b&w")      # once again

print "Done."		# and that's it.

