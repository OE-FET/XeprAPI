# -*- coding: utf-8 -*-

#
# randGrad.py          (c) Copyright 2012, Bruker BioSpin
#
# This script demonstrates how to
#       - build experiments from within a Python script
#       - retrieve data acquired by Xepr
#       - construct 2D datasets from 1D data acquired by Xepr
#       - read and set experiment parameters, both scalar and multi-dimensional
#       - read parameter limits
#       - interact with the Xepr operator
#       - poll the experiment state
#       - use third-party modules to visualize data
#
#
# Note: Prior to running any Xepr API scripts, the Xepr API has to be
#       enabled once in Xepr by selecting the menu item "Enable Xepr API"
#       from the "XeprAPI" sub-menu of the "Processing" menu. However,
#       if the script is run from within Xepr (menu item "Run XeprAPI Script"),
#       the API will be enabled automatically.
#


# pulse experiment or CW experiment?
isPulseExp = True


# minimum/maximum gradient
minGrad,maxGrad = (1.0, 20.0)


NUMBER_OF_SLICES = 25 		# run the 1D experiment repeatedly (to create a 2D dataset)


# for pulse experiment: pulse table presets
if isPulseExp:
    pulsePosLen = ((0,20), (40,20), (80,20))    # tuples of pulse position and length [ns]


import os,sys; sys.path.insert(0, os.popen("Xepr --apipath").read())  # this locates the XeprAPI module

import XeprAPI              # load the Xepr API module

import numpy as NP          # powerful array module for Python

import time                 # system modules


Xepr=XeprAPI.Xepr()  		# start talking to Xepr using the API



# build new experiment
print "Building the experiment..."
if isPulseExp:
    exp = Xepr.XeprExperiment("PulseExp", exptype="Pulse",
                              axs1="Field", ordaxs="Transient recorder",
                              addgrad=True)
else:    # for CW
    exp = Xepr.XeprExperiment("CWExp", exptype="C.W.",
                          axs1="Field", ordaxs="Signal channel",
                          addgrad=True)
print "done."



# preset the pulse table (if we're going to run a pulse experiment)
if isPulseExp:
    pattEdit = exp["*ftEpr.PatternEdit"]        # object for pulse table access
    exp['*ftEpr.ChannelSlct'].value = "Acquisition Trigger" # select "Acquisition Trigger" pulse table
    acqPos  = sum(pulsePosLen[-1])              # position of the aquisition trigger
    pattEdit[0, 0] = acqPos + 500               # add 500 ns and set up the acquisition trigger pulse
    pattEdit[0, 1] = 512                        # length = 512 [ns]

    exp['*ftEpr.ChannelSlct'].value = 1         # select '+x' pulse channel (could also write '+x' instead of the number 1)
    for idx,(pulsepos,pulselen) in enumerate(pulsePosLen):
        pattEdit[idx, 0] = pulsepos             # set pulse position (1st row of the table)
        pattEdit[idx, 1] = pulselen             # set corresponding pulse length (2nd row)




# try to access gradient unit parameters
try:
    psi = exp["AnglePsi"]             # object for accessing "AnglePsi" parameter
    psi.value = 0.0                   # preset parameter
    phi = exp["GradientPhi"]          # object for accessing "GradientPhi" parameter
    minPhi,maxPhi = (phi.aqGetParMinValue(), phi.aqGetParMaxValue())     # get angle limits
    theta = exp["GradientTheta"]      # object for accessing "GradientTheta" parameter
    minTheta,maxTheta = (theta.aqGetParMinValue(), theta.aqGetParMaxValue())     # get angle limits
except XeprAPI.ParameterError:
    print "We do not seem to have a (working) gradient...giving up."
    sys.exit(1)



# show the parameter panel so the user can change some experiment parameters manually
Xepr.XeprCmds.aqParOpen()


Xepr.printLn("Modify the 1D experiment parameters to your liking.")         # could also show a GUI dialog here using
Xepr.printLn("Please start the experiment when ready to continue.")         # toolkits like PyQT, PyGTK, wxPython etc.



# now start the sequence of acquisitions
slice_numbers = range(NUMBER_OF_SLICES)
for slice_no in slice_numbers:

    # set random gradient (within limits)
    psi.value = NP.random.uniform(low = minGrad, high = maxGrad)
    # set random Phi angle
    phi.value = NP.random.uniform(low = minPhi, high = maxPhi)
    # set random Theta angle
    theta.value = NP.random.uniform(low = minTheta, high = maxTheta)


    # if in pulse mode: have the last pulse of the sequence "move"
    if isPulseExp and slice_no > 0:
        lastpulseidx = len(pulsePosLen)-1
        pattEdit[lastpulseidx, 0] = pattEdit[lastpulseidx, 0] + 10.0 # by 10 ns/slice


    # now run the 1D experiment and wait for it to complete
    if slice_no == 0:               # the first experiment is started by the Xepr operator
        while not exp.isRunning:    # poll experiment state
            time.sleep(1e-3)        # sleep for e.g. 1 ms
        Xepr.printLn("Running the 1D experiment %u times...please be patient..." % NUMBER_OF_SLICES)
        print "Acquiring the 1st slice (of %u)..." % NUMBER_OF_SLICES
        while exp.isRunning:        # poll experiment state
            time.sleep(1e-3)        # sleep for e.g. 1 ms
    else:
        print "Acquiring the %u. slice (of %u)..." % (slice_no+1, NUMBER_OF_SLICES)
        exp.aqExpRunAndWait()       # the other slices are acquired by the script

    # set progress bar accordingly
    Xepr.workIndex((slice_no+1)*100.0/NUMBER_OF_SLICES)

    # get 1D dataset for this run
    dset1D = Xepr.XeprDataset()


    # create 2D dataset as soon as we know the abscissa size of the 1D dataset
    if not "dset2D" in globals():       # do that only once
        dset2D = Xepr.XeprDataset(size=(dset1D.X.shape[0], NUMBER_OF_SLICES), iscomplex=dset1D.isComplex)
        dset2D.X = dset1D.X         # copy the 1D abscissa into the 2D dataset
        dset2D.Y = slice_numbers    # and use the slice number indices as the 2nd abscissa



    # insert the 1D ordinate data into the 2D dataset
    dset2D.O[slice_no][:] = dset1D.O[:]


# set the name of the dataset
dset2D.setTitle("My_2D_result")

# transfer the 2D dataset to Xepr's result dataset
dset2D.update(xeprset="result", refresh=True)     # (and refresh the GUI)



# hide primary and secondary datasets in Xepr, show result set only
Xepr.XeprCmds.vpCurrent(-1, "Primary", 0)
Xepr.XeprCmds.vpCurrent(-1, "Secondary", 0)



# and that's it.
print "Done."
Xepr.printLn("Completed %u runs of a 1D experiment to form a 2D dataset." % NUMBER_OF_SLICES)


# try to also plot the data using a third party toolkit, e.g. matplotlib
try:
    import matplotlib
    matplotlib.interactive(True)
    import pylab
    for orddata in dset2D.O[:5]:                # plot up to five slices here
        pylab.plot(dset2D.X, orddata.real)      # show only the real part (for complex data)
        pylab.show()
except:                                 # if for some reason (e.g. matplotlib is not installed)
    pass                                # we cannot plot the data using pylab - give up silently
