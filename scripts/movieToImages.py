#! /usr/bin/python

import cv
import sys

if len( sys.argv ) != 4:
    print "Usage:", sys.argv[ 0 ], "movie outputDir filenameRoot"
else:
    movieFilename = sys.argv[ 1 ]
    outputDir = sys.argv[ 2 ]
    filenameRoot = sys.argv[ 3 ]

    videoCapture = cv.CaptureFromFile( movieFilename )

    movieDescription = outputDir + "/\n"

    imageIdx = 0
    frame = cv.QueryFrame( videoCapture )
    while frame != None:
        filename = "{0}{1:03}.ppm".format( filenameRoot, imageIdx )
        fullFilename = outputDir + "/" + filename
        cv.SaveImage( fullFilename, frame )
        
        # Build up a list of the frames in the movie
        movieDescription = movieDescription + filename + "\n"

        # Get next frame
        frame = cv.QueryFrame( videoCapture )
        imageIdx = imageIdx + 1

    movieDescriptionFile = open( outputDir + "/" + filenameRoot + ".txt", "w" )
    movieDescriptionFile.write( movieDescription )
    movieDescriptionFile.close()
