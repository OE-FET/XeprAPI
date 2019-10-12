# -*- coding: utf-8 -*-

#
# 1Dto2D.py          (c) Copyright 2012, Bruker BioSpin
#
# This script demonstrates how to
#       - access and run Xepr experiments
#       - process 1D data acquired by Xepr using Python
#       - construct 2D datasets from a set of 1D datasets
#       - control hardware units not supported by Xepr using Python
#
#
# Note: Prior to running any Xepr API scripts, the Xepr API has to be
#       enabled once in Xepr by selecting the menu item "Enable Xepr API"
#       from the "XeprAPI" sub-menu of the "Processing" menu. However,
#       if the script is run from within Xepr (menu item "Run XeprAPI Script"),
#       the API will be enabled automatically.
#

NUMBER_OF_RUNS = 10 		# run the experiment repeatedly


USE_EXTERNAL_UNITS = False  # control external instruments?


import os,sys; sys.path.insert(0, os.popen("Xepr --apipath").read())  # this locates the XeprAPI module

import XeprAPI              # load the Xepr API module

import numpy as NP			# powerful array module for Python
import socket				# Python module for network communication 
try:
    import visa				# module for communication via GPIB, USB, RS232,...
except:
    print "could not load 'visa' module, won't be able to access VISA units"
    print "(there probably is no such module installed)"


########## utility functions etc. ###########################

def moving_average(dset, winsize=10):
    win=NP.repeat(1.0/winsize, winsize)
    dset.O = NP.convolve(dset.O, win, mode="same")
   
#############################################################




#############################################################
# first, establish connection to external hardware units 
# no matter if they are supported by Xepr or not

if USE_EXTERNAL_UNITS:
    # e.g. some custom sample changer/autosampler (via Ethernet)
    # on IP address 192.168.1.100, port number 7070
    try:
        samplechanger = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        samplechanger.connect(("192.168.1.100", 7070))
    except:
        samplechanger = None    # cannot access sample changer for some reason

    # and e.g. some power supply via GPIB
    # on GPIB address 12
    try:
        powersupply = visa.instrument("GPIB::12")
    except:
        powersupply = None      # cannot access powersupply for some reason

    # and finally, maybe, a thermometer via USB
    try:
        thermometer = visa.instrument("USB::3")
    except:
        thermometer = None      # cannot access thermometer for some reason

#############################################################




Xepr=XeprAPI.Xepr()  			# start talking to Xepr using the API



# suppose an experiment (1D) is already set up in Xepr...
cur_exp = Xepr.XeprExperiment()



# now start the sequence of acquisitions
for run_no in range(NUMBER_OF_RUNS):
    print "Run %u in progress..." % run_no

    
    # control the external instruments (if any)
    if USE_EXTERNAL_UNITS:
        # e.g. have the sample changer insert a new sample
        if samplechanger:
            samplechanger.send("SAMPLE:%u\n" % run_no)
        # and e.g. control the power supply (set random voltage)
        if powersupply:
            powersupply.write("set:channel1:voltage:%.fV" % (NP.random.rand()*10))


    # now run the 1D experiment and wait for it to complete
    cur_exp.aqExpRunAndWait()

    
    # then maybe read the temperature from the USB thermometer (if attached)
    if USE_EXTERNAL_UNITS:
        if thermometer:
            print "Current temperature: %sK" % thermometer.ask("sensor1:kelvin?")


    # get dataset for this run
    dset1D = Xepr.XeprDataset()


    # create 2D dataset as soon as we know the abscissa size of the 1D dataset
    if not "dset2D" in globals():       # do that only once
        dset2D = Xepr.XeprDataset(size=(dset1D.X.shape[0], NUMBER_OF_RUNS), iscomplex=dset1D.isComplex)
        dset2D.X = dset1D.X         # copy the 1D abscissa into the 2D dataset
        dset2D.Y = range(NUMBER_OF_RUNS)    # and use the run number indices as the 2nd abscissa
    
           
    # apply some post-processing, e.g. apply a moving average filter
    # (using Python methods only)
    moving_average(dset1D, winsize=10)

    # insert the 1D ordinate data into the 2D dataset
    dset2D.O[run_no][:] = dset1D.O[:]



# transfer the 2D dataset to Xepr's secondary dataset
dset2D.update(refresh=True, xeprset="secondary")     # (and refresh the GUI)



# hide primary Xepr dataset, show secondary set only
Xepr.XeprCmds.vpCurrent(-1, "Primary", 0)



# and that's it.
print "Done."



# now save the 2D ordinate data to disk (as a Python object)
# for further processing or archiving etc.
NP.save("AllExperiments.npy", dset2D.O)


