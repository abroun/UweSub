#-------------------------------------------------------------------------------
# Module for determining the AUVs position in a rectangular pool by using
# the sonar.
#-------------------------------------------------------------------------------

import sys
import time
import math

# Add common packages directory to path
sys.path.append( "../" )
from SubControllerConfig import SubControllerConfig
import Maths

class SonarLocator:
    
    MAX_TIME_BETWEEN_SCANS = 30.0
    SCAN_RANGE = 10
    NUM_BINS = 400
    GAIN = 0.1
    
    # All angles here are like compass bearings so 0 degrees is north
    # and angles increase in a clock-wise direction
    
    SONAR_HEADING_OFFSET = Maths.degToRad( 0.0 )    # Offset from sub heading to sonar
    POOL_HEADING = Maths.degToRad( 184.0 )    # Heading of the pool in degrees converted to radians
    
    #---------------------------------------------------------------------------
    def __init__( self, playerCompass, playerSonar, config = SubControllerConfig() ):
        
        self.config = config
        self.playerCompass = playerCompass
        self.playerSonar = playerSonar
        self.lastScanTime = time.time()
        self.lastSonarFrameTime = 0
        self.waitingForScan = False
        self.numFailedScans = 0
        self.rebootStartTime = 0
        self.rebooting = False
   
    #---------------------------------------------------------------------------   
    def startScan( self ):
        
        subHeading = self.playerCompass.pose.pyaw
        headingDiff = subHeading - self.POOL_HEADING    # Diff from pool to sub heading
        
        # Scan when the sub is aligned with the pool to find the bottom right corner
        startScanAngle = self.SONAR_HEADING_OFFSET + Maths.degToRad( 315.0 ) - headingDiff # (Maths.degToRad( 80.0 ) - headingDiff)
        endScanAngle = self.SONAR_HEADING_OFFSET + Maths.degToRad( 45.0 ) - headingDiff # (Maths.degToRad( 190.0 ) - headingDiff)
        
        startScanAngle = subHeading + Maths.degToRad( 260.0 ) - Maths.degToRad( 275.0 )
        endScanAngle = subHeading + Maths.degToRad( 10.0 ) - Maths.degToRad( 275.0 )
        
        print "From", Maths.radToDeg( startScanAngle ), "To", Maths.radToDeg( endScanAngle )
        
        # Normalise the start and end scan angle
        while startScanAngle < 0.0:
            startScanAngle += 2.0*math.pi
        while startScanAngle >= 2.0*math.pi:
            startScanAngle -= 2.0*math.pi
            
        while endScanAngle < 0.0:
            endScanAngle += 2.0*math.pi
        while endScanAngle >= 2.0*math.pi:
            endScanAngle -= 2.0*math.pi
        
        # Configure the sonar
        self.playerSonar.set_config( self.SCAN_RANGE, self.NUM_BINS, self.GAIN )
        
        # Start the scan
        self.playerSonar.scan( startScanAngle, endScanAngle )
        
        print "Requested scan"
        print "SubHeading", Maths.radToDeg( subHeading )
        print "From", Maths.radToDeg( startScanAngle ), "To", Maths.radToDeg( endScanAngle )
        
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
        
        curTime = time.time()
        
        # Perform a sonar scan
        if self.waitingForScan:
            
            if curTime - self.lastScanTime > self.MAX_TIME_BETWEEN_SCANS:
                print "Warning: Timed out waiting for scan, requesting new one"
                self.numFailedScans += 1
                
                if self.numFailedScans <= 1:
                    self.startScan()
                else:
                    self.playerSonar.say( "REBOOT" )
                    time.sleep( 6.0 )
                    self.numFailedScans = 0
            else:
                if self.isNewSonarFrameAvailable():
                    self.waitingForScan = False
                    self.numFailedScans = 0
                    self.lastSonarFrameTime = self.playerSonar.info.datatime
                    print "Got scan"
            
        else:
            self.startScan()
            
            
            
        