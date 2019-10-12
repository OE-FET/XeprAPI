# -*- coding: utf-8 -*-

#
# saveScans.py          (c) Copyright 2013, Bruker BioSpin
#
# This script demonstrates how to
#       - save individual scans of an experiment to data files
#       - retrieve data acquired by Xepr
#       - read experiment parameters
#       - poll the experiment state
#
#
# Note: Prior to running any Xepr API scripts, the Xepr API has to be
#       enabled once in Xepr by selecting the menu item "Enable Xepr API"
#       from the "XeprAPI" sub-menu of the "Processing" menu. However,
#       if the script is run from within Xepr (menu item "Run XeprAPI Script"),
#       the API will be enabled automatically.
#




# template for the data file name
filename_template = "/tmp/scan%04u.npy"

import os,sys; sys.path.insert(0, os.popen("Xepr --apipath").read())  # this locates the XeprAPI module

import XeprAPI
import time
import numpy as NP

xepr=XeprAPI.Xepr()


try:
  exp=xepr.XeprExperiment()
except:
  print "Please setup a 1D experiment (number of scans>1, replace mode on) before you run the script"
  sys.exit(1)

# get total number of scans
scansToDo = int(exp['NbScansToDo'].value)	
# get parameter object for "Scans Done"
scansDonePar = exp['NbScansDone']		

print "Waiting for experiment to start..."

currentscan = 0
while currentscan < scansToDo:
      
  # wait for the experiment to run      
  while not exp.isRunning:	
      pass

  # then request a break
  exp.aqExpPause()		
  
  # wait for the experiment to be paused
  while not exp.isPaused:	
      time.sleep(1e-3)	# short delay while polling the state

  
  # make sure "Scans Done" is updated
  exp.aqExpSync()
  while scansDonePar.value==currentscan: 
      print 'wait for "Scans Done" to be updated'
      time.sleep(1e-3)  # short delay while waiting for the update
  
  currentscan = scansDonePar.value
  print "acquired scan %u" % currentscan
  
  # retrieve the data and save it to a file
  dset=xepr.XeprDataset()
  ordinate=dset.O
  NP.save(filename_template % currentscan, ordinate)
  
  # continue experiment
  exp.aqExpRun()	

print "Done."  
    
