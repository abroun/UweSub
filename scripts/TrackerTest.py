#! /usr/bin/python

import cv
from ColourTracker import ColourTracker

print "Yo"

videoCapture = cv.CaptureFromFile( "../data/buoy.avi" )

print "Opened video.."

tracker = ColourTracker()

print "loaded and created tracker..."

#cv.SetCaptureProperty( videoCapture, cv.CV_CAP_PROP_POS_FRAMES, 1300 )

frame = cv.QueryFrame( videoCapture )
while frame != None:
    tracker.processFrame( frame )
    frame = cv.QueryFrame( videoCapture )

print "Done!"