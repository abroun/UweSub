""" Attempts to track the Buoy using just colour """

import cv
import math

#-------------------------------------------------------------------------------
class BuoyData:

    def __init__( self, visible, centreX, centreY, radius ):
        self.visible = visible
        self.centreX = centreX
        self.centreY = centreY
        self.radius = radius

#-------------------------------------------------------------------------------
class ColourTracker:

    def __init__( self ):
        self.reset()
        self.trackedHue = (15.0 / 360.0)*255.0
        self.maxAbsHueDiff = (5.0 / 360.0)*255.0
        self.calculateRadius = False

    def reset( self ):
        self.buoyData = BuoyData( False, 0.0, 0.0, 0.0 )
        
    def processFrame( self, frame ):
        
        # This routine expects BGR frames...
        
        # Convert the frame to HSV
        hsvFrame = cv.CreateImage( ( frame.width, frame.height ), frame.depth, frame.nChannels )
        cv.CvtColor( frame, hsvFrame, cv.CV_BGR2HSV )
        
        # Loop through each pixel in the frame looking for orange pixels
        centreX = 0
        centreY = 0
        numMatchingPixels = 0
        matchingPixelList = []
        
        for y in [i*2 for i in range( hsvFrame.height/2 ) ]:
            for x in [i*2 for i in range( hsvFrame.width/2 ) ]:
            
                pixel = hsvFrame[ y, x ]
                pixelHue = pixel[ 0 ]
                
                absHueDiff = abs( self.trackedHue - pixelHue )
                if absHueDiff <= self.maxAbsHueDiff:
                    centreX = centreX + x
                    centreY = centreY + y
                    numMatchingPixels = numMatchingPixels + 1
                    
                    if self.calculateRadius:
                        matchingPixelList.append( ( x, y ) )
        
        # Return the centre of mass of all the 'orangish' pixels
        #print "Num Matching Pixels = " + str( numMatchingPixels )
        if numMatchingPixels > 0:
            centreX /= numMatchingPixels
            centreY /= numMatchingPixels
            self.buoyData = BuoyData( True, centreX, centreY, 10.0 )
            
            # Set the radius as the standard deviation of the blob
            if self.calculateRadius:
                squaredDistanceSum = 0
                for pixelCoords in matchingPixelList:
                    squaredDistanceSum = squaredDistanceSum \
                        + ( pixelCoords[ 0 ] - centreX )**2 + ( pixelCoords[ 1 ] - centreY )**2
                
                variance = squaredDistanceSum / numMatchingPixels
                self.buoyData.radius = math.sqrt( variance )
        else:
            self.buoyData.visible = False

    def getBuoyData( self ):
        return self.buoyData

    def isBuoyVisible( self ):
        return self.buoyData.visible

    def getBuoyPos( self ):
        return ( self.buoyData.centreX, self.buoyData.centreY )
        
    def getBuoyRadius( self ):
        return self.buoyData.radius