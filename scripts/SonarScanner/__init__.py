#-------------------------------------------------------------------------------
# Module for producing sonar scans. If a depth sensor is provided then the 
# module will stop performing scans if the AUV is not below a safe depth
#-------------------------------------------------------------------------------

import cv
import time

# Add common packages directory to path
sys.path.append( "../" )
from SubControllerConfig import SubControllerConfig
import Maths

#-------------------------------------------------------------------------------
class SonarScanner:
    
    #---------------------------------------------------------------------------
    def __init__( self, logger, playerSonar, playerDepthSensor = None, 
        config = SubControllerConfig() ):
            
        self.logger = logger
        self.config = config
        self.playerSonar = playerSonar
        self.playerDepthSensor = playerDepthSensor
        self.lastScanTime = time.time()
        self.lastSonarFrameTime = 0
        self.waitingForScan = False
        self.numFailedScans = 0
        self.rebootStartTime = 0
        self.rebooting = False
        self.sonarImage = None  # A grayscale OpenCV image from the sonar
        self.active = True
        
        self.scanStartAngle = Maths.degToRad( 0.0 )
        self.scanEndAngle = Maths.degToRad( 90.0 )
   
    #---------------------------------------------------------------------------
    def setActive( self, active ):
        self.active = active
   
    #---------------------------------------------------------------------------
    def setSonarConfig( scanRange, numBins, gain ):
        self.scanRange = scanRange
        self.numBins = numBins
        self.gain = gain
    
    #---------------------------------------------------------------------------
    def setScanAngleRange( scanStartAngle, scanEndAngle ):
        self.scanStartAngle = scanStartAngle
        self.scanEndAngle = scanEndAngle
   
    #---------------------------------------------------------------------------   
    def startScan( self ):
        
        if not self.active:
            return
        
        if self.playerDepthSensor != None:
            if self.playerDepthSensor.info.datatime == 0 \
                or self.playerDepthSensor.pos < self.config.safeSonarDepth:
                return  # Too high to perform the scan (or no depth data yet)
        
        # Configure the sonar
        self.playerSonar.set_config( self.scanRange, self.numBins, self.gain )
        
        # Start the scan
        self.playerSonar.scan( self.scanStartAngle, self.scanEndAngle )
        
        #print "Requested scan"
        #print "SubHeading", Maths.radToDeg( subHeading )
        #print "From", Maths.radToDeg( scanStartAngle ), "To", Maths.radToDeg( scanEndAngle )
        
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
                logger.logMsg( "SonarScanner: Timed out waiting for scan, requesting new one" )
                self.numFailedScans += 1
                
                if self.numFailedScans <= self.NUM_FAILED_SCANS_BETWEEN_REBOOTS:
                    self.startScan()
                else:
                    logger.logMsg( "SonarScanner: Trying to reboot sonar" )
                    self.playerSonar.say( "REBOOT" )
                    time.sleep( 6.0 )
                    self.numFailedScans = 0
            else:
                if self.isNewSonarFrameAvailable():
                    self.waitingForScan = False
                    self.numFailedScans = 0
                    self.lastSonarFrameTime = self.playerSonar.info.datatime
                    
                    # Get image from sonar
                    self.sonarImage = cv.CreateImageHeader( ( self.playerSonar.width, self.playerSonar.height ), cv.IPL_DEPTH_8U, 1 )       
                    cv.SetData( self.sonarImage, self.playerSonar.image[:self.playerSonar.image_count], self.playerSonar.width )
            
        else:
            self.startScan()
    
        