#-------------------------------------------------------------------------------
# Script for descending to a given depth whilst taking sonar scans
#-------------------------------------------------------------------------------

import sys
import time
import math
import string
import os
from datetime import datetime
import cv
import playerc

from ControlScripts import ControlScript

# Add common packages directory to path
sys.path.append( "../" )
from Controllers import Arbitrator
from SonarScanner import SonarScanner
import Maths

#-------------------------------------------------------------------------------
class ImageCaptureScript( ControlScript ):
    
    STATE_PERFORMING_SCANS = "Performing Scans"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3d, 
        playerDepthSensor, playerSonar, playerFrontCamera ):
        
        ControlScript.__init__( self, config, logger, 
            playerPos3d, playerCompass = None, 
            playerDepthSensor = playerDepthSensor, playerSonar = playerSonar, 
            playerFrontCamera = playerFrontCamera )
            
        self.sonarScanner = SonarScanner( 
            logger, playerSonar, 
            playerDepthSensor, config )
        
        self.setState( self.STATE_PERFORMING_SCANS )
        self.lastCameraFrameTime = 0.0
        self.lastSonarFrameTime = 0.0
        self.lastCameraImageSaveTime = 0.0
        
        self.sonarImagesDir = string.Template( config.sonarImagesDir ).safe_substitute( os.environ )
        self.cameraImagesDir = string.Template( config.cameraImagesDir ).safe_substitute( os.environ )
        
        self.sonarScanner.setSonarConfig( 
            self.config.IC_Script_sonarRange, 
            self.config.IC_Script_sonarNumBins, 
            self.config.IC_Script_sonarGain )
        self.sonarScanner.setScanAngleRange( 
            self.config.IC_Script_sonarScanStartAngle, 
            self.config.IC_Script_sonarScanEndAngle )
    
    #---------------------------------------------------------------------------
    def isNewSonarFrameAvailable( self ):
        if self.playerSonar == None:
            return False
        else:
            return self.lastSonarFrameTime != self.playerSonar.info.datatime
            
    #---------------------------------------------------------------------------
    def isNewCameraFrameAvailable( self ):
        if self.playerFrontCamera == None:
            return False
        else:
            return self.lastCameraFrameTime != self.playerFrontCamera.info.datatime
    
    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.state == self.STATE_PERFORMING_SCANS:

            if self.config.IC_Script_enableSonar:
                self.sonarScanner.update()
                if self.isNewSonarFrameAvailable():
                    self.lastSonarFrameTime = self.playerSonar.info.datatime
                    
                    # Save the sonar image
                    sonarImageFilename = "{0}/{1}.png".format( 
                        self.sonarImagesDir, str( datetime.now() ) )
                    cv.SaveImage( sonarImageFilename, self.sonarScanner.sonarImage )
                    
            if self.config.IC_Script_enableCamera:
                if curTime - self.lastCameraImageSaveTime > 1.0/self.config.IC_Script_numImagesSavedPerSecond \
                    and self.isNewCameraFrameAvailable():

                    self.lastCameraFrameTime = self.playerFrontCamera.info.datatime
                    self.lastCameraImageSaveTime = curTime
                    
                    # Save the camera image
                    cameraImageFilename = "{0}/{1}.png".format( 
                        self.cameraImagesDir, str( datetime.now() ) )
                    
                    if self.playerFrontCamera.compression != playerc.PLAYER_CAMERA_COMPRESS_RAW:
                        self.playerFrontCamera.decompress()
                
                    if self.playerFrontCamera.compression != playerc.PLAYER_CAMERA_COMPRESS_RAW:
                        print "Error: Unable to decompress frame"
                        sys.exit( -1 )

                    # Give the image to OpenCV as a very inefficient way to
                    # save it as a jpeg
                    rgbImage = cv.CreateImageHeader( ( self.playerFrontCamera.width, self.playerFrontCamera.height ), cv.IPL_DEPTH_8U, 3 )       
                    cv.SetData( rgbImage, self.playerFrontCamera.image[:self.playerFrontCamera.image_count], self.playerFrontCamera.width*3 )
            
                    # Resize the image to 160x120
                    zoom = 0.5
                    if zoom != 1.0:
                        scaledImage = cv.CreateImage( 
                            ( int( rgbImage.width*zoom ), 
                                int ( rgbImage.height*zoom ) ), 
                            rgbImage.depth, rgbImage.nChannels )
                    
                        cv.Resize( rgbImage, scaledImage )
                        rgbImage = scaledImage
            
                    # Image must be converted to bgr for saving with OpenCV
                    bgrImage = cv.CreateImage( ( rgbImage.width, rgbImage.height ), cv.IPL_DEPTH_8U, 3 )
                    cv.CvtColor( rgbImage, bgrImage, cv.CV_RGB2BGR )
                    cv.SaveImage( cameraImageFilename, bgrImage )

        
