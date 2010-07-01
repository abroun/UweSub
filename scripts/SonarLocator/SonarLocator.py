#-------------------------------------------------------------------------------
# Module for determining the AUVs position in a rectangular pool by using
# the sonar.
#-------------------------------------------------------------------------------

import sys
import time
import math
import cv

from CornerFinder import findCorner as CF_FindCorner

# Add common packages directory to path
sys.path.append( "../" )
from SubControllerConfig import SubControllerConfig
from SonarScanner import SonarScanner
import Maths

#-------------------------------------------------------------------------------
class SonarLocator:
    
    SCAN_RANGE = 4
    NUM_BINS = 300
    GAIN = 0.3
    
    # All angles here are like compass bearings so 0 degrees is north
    # and angles increase in a clock-wise direction
    
    #SONAR_HEADING_OFFSET = Maths.degToRad( 0.0 )    # Offset from sub heading to sonar
    POOL_HEADING = Maths.degToRad( 306.0 )    # Heading of the pool in degrees converted to radians
    IDEAL_SCAN_START_ANGLE = Maths.degToRad( 350.0 )
    IDEAL_SCAN_END_ANGLE = Maths.degToRad( 100.0 )
    
    #---------------------------------------------------------------------------
    def __init__( self, logger, playerCompass, playerSonar, 
        playerDepthSensor = None, config = SubControllerConfig() ):
        
        self.logger = logger
        self.config = config
        self.playerCompass = playerCompass
        self.playerSonar = playerSonar
        self.lastSonarFrameTime = 0
        
        self.sonarScanner = SonarScanner( logger, playerSonar, 
            playerDepthSensor, config )
        self.sonarScanner.setActive( False )
        self.subPos = None
        self.detectedLines = None 
        self.thresholdedSonarImage = None 
        self.cornerPos = None
        self.sonarImage = None

    #---------------------------------------------------------------------------
    def isNewSonarFrameAvailable( self ):
        if self.playerSonar == None:
            return False
        else:
            return self.lastSonarFrameTime != self.playerSonar.info.datatime
    
    #---------------------------------------------------------------------------
    def configureSonar():
        
        subHeading = self.playerCompass.pose.pyaw
        angleOffset = subHeading - self.POOL_HEADING    # Diff from pool to sub heading
        
        # Scan when the sub is aligned with the pool to find the bottom right corner
        scanStartAngle = self.IDEAL_SCAN_START_ANGLE - angleOffset
        scanEndAngle = self.IDEAL_SCAN_END_ANGLE - angleOffset
    
        scanStartAngle = Maths.normaliseAngle( scanStartAngle, 0.0 )
        scanEndAngle = Maths.normaliseAngle( scanEndAngle, 0.0 )
        
        #print "From", Maths.radToDeg( startScanAngle ), "To", Maths.radToDeg( endScanAngle )
        
        # Configure the sonar scanner
        self.sonarScanner.setSonarConfig( self.SCAN_RANGE, self.NUM_BINS, self.GAIN )
        self.sonarScanner.setScanAngleRange( scanStartAngle, scanEndAngle )
        
    #---------------------------------------------------------------------------
    def update( self ):

        if self.playerCompass.info.datatime != 0:
            self.compassStartTime = self.playerCompass.info.datatime
        else:
            # Don't start until we have compass data
            return

        if not self.sonarScanner.active: 
            self.configureSonar()
            self.sonarScanner.setActive( True )
        else:
            if self.isNewSonarFrameAvailable():
                self.configureSonar()   # Prepare for next sonar scan
                self.lastSonarFrameTime = self.playerSonar.info.datatime
                
                self.sonarImage = self.sonarScanner.sonarImage
                    
                # Run the corner finder on the image
                #self.detectedLines, self.thresholdedSonarImage, self.cornerPos = \
                #    CF_FindCorner( self.sonarImage )
                        
                if self.cornerPos != None:
                    #self.subPos
                    pass
