#-------------------------------------------------------------------------------
# Module that attempts to locate a corner in a grayscale sonar image
#-------------------------------------------------------------------------------

import math
import cv

#-------------------------------------------------------------------------------
# Accepts an 8-bit grayscale image as input and returns the most likely corner
def findCorner( image ):
    
    # black_sonar_pool.png
    #THRESHOLD = 12
    #HOUGH_THRESHOLD = 75
    
    # black_sonar_90m.png
    THRESHOLD = 32
    HOUGH_THRESHOLD = 30

    MIN_INTERSECTION_ANGLE = 85.0*math.pi/180.0
    MAX_INTERSECTION_ANGLE = 95.0*math.pi/180.0
    IDEAL_INTERSECTION_ANGLE = (MIN_INTERSECTION_ANGLE + MAX_INTERSECTION_ANGLE)/2.0
    
    thresholdedImage = cv.CloneImage( image )
    
    
    #cv.Canny( thresholdedImage, thresholdedImage, 32, 128 )
    cv.Threshold( thresholdedImage, thresholdedImage, THRESHOLD, 255, cv.CV_THRESH_BINARY )
    lines = cv.HoughLines2( thresholdedImage, cv.CreateMemStorage(), cv.CV_HOUGH_STANDARD, 
        1.0, 5.0*math.pi/180.0, HOUGH_THRESHOLD )
     
    linesCopy = [(line[0], line[1]) for line in lines]
    
    # Find intersections
    maxIntersectionRating = -1.0
    cornerPos = None
    
    for lineIdx in range( lines ):
        
        line = lines[ lineIdx ]
        
        for otherLineIdx in range( lineIdx + 1, lines ):
            
            otherLine = lines[ otherLineIdx ]
            angleDiff = math.pi - ( line[ 1 ] - otherline[ 1 ] )
            
            # Normalise the angle to the range -pi to +pi
            normAngleDiff = angleDiff
            while normAngleDiff >= math.pi:
                normAngleDiff -= 2.0*math.pi
            while normAngleDiff < -math.pi:
                normAngleDiff += 2.0*math.pi
            
            absAngleDiff = abs( normAngleDiff )
            if absAngleDiff > MIN_INTERSECTION_ANGLE \
                and absAngleDiff < MAX_INTERSECTION_ANGLE:
                
                a1 = line[ 0 ]
                a2 = line[ 1 ]
                c = math.sqrt( a1*a1 + a2*a2 - 2*a1*a2*cos( angleDiff ) )
                
                L1 = math.asin( (a1*math.sin( math.pi - angleDiff )) / c )
                l1 = (math.sin( (math.pi/2.0) - L1 ) * c) / math.sin( angleDiff )
                
                cornerRho = math.sqrt( l1*l1 + a1*a1 )
    
                # Convert the angle diff to a value between 0 for far away
                # from the ideal intersection angle and 1 for bang on the
                # ideal intersection angle
                intersectionRating = 1.0 - abs( absAngleDiff - IDEAL_INTERSECTION_ANGLE )
                if intersectionRating > maxIntersectionRating:
                    maxIntersectionRating = intersectionRating
                    
    del lines
    
    return linesCopy, thresholdedImage
    
    