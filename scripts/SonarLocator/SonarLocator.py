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
import Maths

class SonarLocator:
    
    MAX_TIME_BETWEEN_SCANS = 30.0
    NUM_FAILED_SCANS_BETWEEN_REBOOTS = 2
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
    def __init__( self, playerCompass, playerSonar, config = SubControllerConfig() ):
        
        self.config = config
        self.playerCompass = playerCompass
        self.playerSonar = playerSonar
        self.lastScanTime = time.time()
        self.lastSonarFrameTime = 0
        self.compassStartTime = 0
        self.waitingForScan = False
        self.numFailedScans = 0
        self.rebootStartTime = 0
        self.rebooting = False
        self.subPos = None
        self.detectedLines = None 
        self.thresholdedSonarImage = None 
        self.cornerPos = None
        self.sonarImage = None
   
    #---------------------------------------------------------------------------   
    def startScan( self ):
        
        subHeading = self.playerCompass.pose.pyaw
        angleOffset = subHeading - self.POOL_HEADING    # Diff from pool to sub heading
        
        # Scan when the sub is aligned with the pool to find the bottom right corner
        scanStartAngle = self.IDEAL_SCAN_START_ANGLE - angleOffset
        scanEndAngle = self.IDEAL_SCAN_END_ANGLE - angleOffset
    
        scanStartAngle = Maths.normaliseAngle( scanStartAngle, 0.0 )
        scanEndAngle = Maths.normaliseAngle( scanEndAngle, 0.0 )
        
        #print "From", Maths.radToDeg( startScanAngle ), "To", Maths.radToDeg( endScanAngle )
        
        # Configure the sonar
        self.playerSonar.set_config( self.SCAN_RANGE, self.NUM_BINS, self.GAIN )
        
        # Start the scan
        self.playerSonar.scan( scanStartAngle, scanEndAngle )
        
        print "Requested scan"
        print "SubHeading", Maths.radToDeg( subHeading )
        print "From", Maths.radToDeg( scanStartAngle ), "To", Maths.radToDeg( scanEndAngle )
        
        self.lastScanTime = time.time()
        self.waitingForScan = True
    
    #---------------------------------------------------------------------------
    def isNewSonarFrameAvailable( self ):
        if self.playerSonar == None:
            return False
        else:
            return self.lastSonarFrameTime != self.playerSonar.info.datatime
    
    #---------------------------------------------------------------------------
    def update( self ):
        
        if self.playerCompass.info.datatime != 0:
            self.compassStartTime = self.playerCompass.info.datatime
        else:
            # Don't start until we have compass data
            return
        
        curTime = time.time()
        
        # Perform a sonar scan
        if self.waitingForScan:
            
            if curTime - self.lastScanTime > self.MAX_TIME_BETWEEN_SCANS:
                print "Warning: Timed out waiting for scan, requesting new one"
                self.numFailedScans += 1
                
                if self.numFailedScans <= self.NUM_FAILED_SCANS_BETWEEN_REBOOTS:
                    self.startScan()
                else:
                    print "Trying to reboot sonar"
                    self.playerSonar.say( "REBOOT" )
                    time.sleep( 6.0 )
                    self.numFailedScans = 0
            else:
                if self.isNewSonarFrameAvailable():
                    self.waitingForScan = False
                    self.numFailedScans = 0
                    self.lastSonarFrameTime = self.playerSonar.info.datatime
                    print "Got scan"
                    
                    # Get image from sonar
                    self.sonarImage = cv.CreateImageHeader( ( self.playerSonar.width, self.playerSonar.height ), cv.IPL_DEPTH_8U, 1 )       
                    cv.SetData( self.sonarImage, self.playerSonar.image[:self.playerSonar.image_count], self.playerSonar.width )
        
                    # Run the corner finder on the image
                    #self.detectedLines, self.thresholdedSonarImage, self.cornerPos = \
                    #    CF_FindCorner( self.sonarImage )
                        
                    if self.cornerPos != None:
                        #self.subPos
                        pass
            
        else:
            self.startScan()
            
            
            
        