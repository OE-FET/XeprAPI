# -*- coding: utf-8 -*-

# 
# DSet2Excel.py          (c) Copyright 2012, Bruker BioSpin
#
# This script demonstrates how to
#       - load Xepr datasets into Xepr using native Xepr commands
#       - use exceptions raised by Xepr API to handle error conditions
#       - access individual slices of 2D datasets
#       - process real and complex ordinate data
#       - export data for use with external software
#
#
# Note: Prior to running any Xepr API scripts, the Xepr API has to be
#       enabled once in Xepr by selecting the menu item "Enable Xepr API"
#       from the "XeprAPI" sub-menu of the "Processing" menu. However,
#       if the script is run from within Xepr (menu item "Run XeprAPI Script"),
#       the API will be enabled automatically.
#


import os,sys; sys.path.insert(0, os.popen("Xepr --apipath").read())  # this locates the XeprAPI module

import XeprAPI			# load Xepr API module

try:
    import xlwt			# third-party module for spreadsheet export
    havexlwt = True
except:
    havexlwt = False




# establish Xepr API
Xepr=XeprAPI.Xepr()




# if dataset file is given load it
if sys.argv[1:]:
  dsname = sys.argv[1]
  assert os.path.exists(dsname), "dataset %s not found!" % dsname
  Xepr.XeprCmds.vpLoad(dsname)      #   actually load it into Xepr
  excel_file = dsname + ".xls"		# file name for corresponding XLS file
else:
  excel_file = "Xeprdata.xls"		# default output file
  dsname = "Xeprdata"
  


# read data from primary viewport (should already contain data at this point)
dset = Xepr.XeprDataset()
if not dset.datasetAvailable():     # no data? -- try to run current experiment (if possible)
    try:
        print "Trying to run current experiment to create some data..."
        Xepr.XeprExperiment().aqExpRunAndWait()
    except XeprAPI.ExperimentError:
        print "No dataset available and no (working) experiment to run...giving up..."
        sys.exit(1)
if not dset.datasetAvailable():
    print "(Still) no dataset available...giving up..."
    sys.exit(1)


# select first slice if dataset is 2D (take entire 1D ordinate otherwise)
ordinate = dset.O[0] if len(dset.O.shape)==2 else dset.O
############################ Xepr stuff ends here ##############################



# create Excel file (or CSV file)
if havexlwt:
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Xepr data (primary viewport)")
else:
    outfd = open(dsname + ".csv", "w")



if havexlwt:        # should be able to write XLS file
    for line, xval in enumerate(dset.X):
        worksheet.write(line, 0, float(xval))
  
    for line, yval in enumerate(ordinate.real):
        worksheet.write(line, 1, float(yval))

    if dset.isComplex:    # add column for complex ordinate
        for line, yval in enumerate(ordinate.imag):
            worksheet.write(line, 2, float(yval))


    print "Writing Xepr data to %s." % excel_file
    workbook.save(excel_file)

else:               # write CSV file otherwise
    if not dset.isComplex:
        for x,y in zip(dset.X, ordinate):
            print >>outfd, "%20f,%20f" % (x,y)
    else:
        for x,yreal,yimag in zip(dset.X, ordinate.real, ordinate.imag):
            print >>outfd, "%20f,%20f,%20f" % (x,yreal,yimag)

    print "Writing Xepr data to %s." % outfd.name
    outfd.close()

 
  

