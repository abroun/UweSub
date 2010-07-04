#! /usr/bin/python

import sys
import string

# Open log file
logFile = open( sys.argv[ 1 ] )
outputFilename = "UWE - " + sys.argv[ 1 ]
outputFile = open( outputFilename, "w" )

# Go through each line
for line in logFile:
    # If it doesn't end in UWE then pass it through to the formatted log file
    if line[ -5: ] != ",UWE\n":
        outputFile.write( line )

logFile.close()
outputFile.close()
