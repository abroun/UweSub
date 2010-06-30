#-------------------------------------------------------------------------------
# Assorted maths functions
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
import math

#-------------------------------------------------------------------------------
def degToRad( degrees ):
    return degrees*math.pi/180.0

#-------------------------------------------------------------------------------
def radToDeg( degrees ):
    return degrees*180.0/math.pi

#-------------------------------------------------------------------------------
# Normalises an angle in radians into the range [lowerBound, lowerBound + 2*PI)
def normaliseAngle( angle, lowerBound ):
    
    normalisedAngle = angle
    while normalisedAngle < lowerBound:
        normalisedAngle += 2.0*math.pi
    while normalisedAngle >= lowerBound + 2.0*math.pi:
        normalisedAngle -= 2.0*math.pi
        
    return normalisedAngle