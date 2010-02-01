#! /usr/bin/python

#-------------------------------------------------------------------------------
# Control program for submarine
#-------------------------------------------------------------------------------

import os
from optparse import OptionParser

import cv
import yaml
from playerc import *
import Profiling

#from ColourTracker import ColourTracker
from RoBoardControl import ColourTracker

#-------------------------------------------------------------------------------
class SubControllerConfig( yaml.YAMLObject ):

    yaml_tag = u'!SubControllerConfig'

    ROBOT_TYPE_REAL = "Real"
    ROBOT_TYPE_SIM = "Sim"

    PLAYER_SERVER_ADDRESS = 'localhost'
    PLAYER_SERVER_PORT = 6665
    
    TRACKED_HUE = 22.0
    MAX_ABS_HUE_DIFF = 6.0
    TRACKED_SATURATION = 70.0
    MAX_ABS_SATURATION_DIFF = 5.0
    TRACKED_VALUE = 60.0
    MAX_ABS_VALUE_DIFF = 15.0

    FORWARD_SPEED = 1.0
    YAW_SPEED = 0.3
    SCREEN_RADIUS_OF_CLOSE_BUOY = 0.2
    
    def __init__( self ):
        self.robotType = self.ROBOT_TYPE_REAL

        self.playerServerAddress = self.PLAYER_SERVER_ADDRESS
        self.playerServerPort = self.PLAYER_SERVER_PORT

        self.trackedHue = self.TRACKED_HUE
        self.maxAbsHueDiff = self.MAX_ABS_HUE_DIFF
        self.trackedSaturation = self.TRACKED_SATURATION
        self.maxAbsSaturationDiff = self.MAX_ABS_SATURATION_DIFF
        self.trackedValue = self.TRACKED_VALUE
        self.maxAbsValueDiff = self.MAX_ABS_VALUE_DIFF

        self.forwardSpeed = self.FORWARD_SPEED
        self.yawSpeed = self.YAW_SPEED
        self.screenRadiusOfCloseBuoy = self.SCREEN_RADIUS_OF_CLOSE_BUOY

#-------------------------------------------------------------------------------
class SubController:

    LEFT = "Left"
    RIGHT = "Right"

    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):

        self.robotType = config.robotType
        self.tracker = ColourTracker()
        self.tracker.setTrackedHue( config.trackedHue, config.maxAbsHueDiff )
        self.tracker.setTrackedSaturation( config.trackedSaturation, config.maxAbsSaturationDiff )
        self.tracker.setTrackedValue( config.trackedValue, config.maxAbsValueDiff )
        
        self.frame = None
        self.lastTurnDirection = self.LEFT
        self.forwardSpeed = config.forwardSpeed
        self.absYawSpeed = abs( config.yawSpeed )
        self.screenRadiusOfCloseBuoy = config.screenRadiusOfCloseBuoy
        
        # Create a client object
        self.playerClient = playerc_client( None, 
            config.playerServerAddress, config.playerServerPort )
        # Connect it
        if self.playerClient.connect() != 0:
            raise playerc_error_str()

        self.playerPos3d = None
        if self.robotType == SubControllerConfig.ROBOT_TYPE_SIM:
            # Create a proxy for position3d:0
            self.playerPos3d = playerc_position3d( self.playerClient, 0 )
            if self.playerPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise playerc_error_str()
        
        self.playerCamera = playerc_camera( self.playerClient, 0 )
        if self.playerCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
            raise playerc_error_str()

        if self.playerClient.datamode( PLAYERC_DATAMODE_PULL ) != 0:
            raise playerc_error_str()
    
        if self.playerClient.set_replace_rule( -1, -1, PLAYER_MSGTYPE_DATA, -1, 1 ) != 0:
            raise playerc_error_str()
    
        print "Connected to Player!"
      
    #---------------------------------------------------------------------------
    def __del__( self ):
        self.shutdown()
      
    #---------------------------------------------------------------------------
    def shutdown( self ):
        if self.playerCamera != None:
            self.playerCamera.unsubscribe()
        if self.playerPos3d != None:
            self.playerPos3d.unsubscribe()
        if self.playerClient != None:
            self.playerClient.disconnect()
            
    #---------------------------------------------------------------------------
    #@Profiling.printTiming
    def getImage( self ):
        self.playerClient.read()

        if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
            self.playerCamera.decompress()
            
        if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
            print( "Error: Unable to decompress frame" );
            return None
       
        cvImage = cv.CreateImageHeader( ( self.playerCamera.width, self.playerCamera.height ), cv.IPL_DEPTH_8U, 3 )       
        cv.SetData( cvImage, self.playerCamera.image[:self.playerCamera.image_count], self.playerCamera.width*3 )

        #if self.robotType != ROBOT_TYPE_REAL:
        #    cv.CvtColor( cvImage, cvImage, cv.CV_RGB2BGR )
        
        return cvImage
        
    #---------------------------------------------------------------------------
    def update( self ):
        newFrameAvailable = False
    
        if self.playerClient.peek( 0 ):
            self.getAndProcessFrame()        
            newFrameAvailable = True
                     
            forwardSpeed = 0.0
            yawSpeed = 0.0

            blobData = self.tracker.getBlobData()
            if blobData.visible:

                halfFrameWidth = self.frame.width / 2.0
                radiusOfCloseBuoy = self.screenRadiusOfCloseBuoy*self.frame.width

                if blobData.centreX < halfFrameWidth * 0.9:
                    command = "Go Left"
                    yawSpeed = self.absYawSpeed
                    self.lastTurnDirection = self.LEFT
                elif blobData.centreX > halfFrameWidth * 1.1:
                    command = "Go Right"
                    yawSpeed = -self.absYawSpeed
                    self.lastTurnDirection = self.RIGHT
                else:
                    if blobData.radius < radiusOfCloseBuoy:
                        command = "Go Forward"
                        forwardSpeed = self.forwardSpeed
                    else:
                        command = "Stay Still"

                print "Buoy Visible at ( " + str( blobData.centreX ) + ", " + str( blobData.centreY ) + " ) - " + command

            else:
                print "Can't see buoy - turning " + self.lastTurnDirection.lower()

                # Turn to search for the buoy
                if self.lastTurnDirection == self.LEFT:
                    yawSpeed = self.absYawSpeed
                else:
                    yawSpeed = -self.absYawSpeed

            # Steer the AUV
            if self.playerPos3d != None:
                self.playerPos3d.set_velocity( 
                    forwardSpeed, 0.0, 0.0, # x, y, z
                    0.0, 0.0, yawSpeed, # roll, pitch, yaw
                    0 )   # State
        
        return newFrameAvailable

    #---------------------------------------------------------------------------
    @Profiling.printTiming
    def getAndProcessFrame( self ):
        
        self.frame = self.getImage()
                
        #cv.CvtColor( frame, frame, cv.CV_RGB2BGR )
        self.processedFrameData = self.tracker.processFrame( self.frame )
        
        #processedFrame = cv.CreateImageHeader( ( self.playerCamera.width, self.playerCamera.height ), cv.IPL_DEPTH_8U, 3 )       
        #cv.SetData( cvImage, processedFrameData, self.playerCamera.width*3 )

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    optionParser = OptionParser()
    optionParser.add_option( "-c", "--config", dest="configFilename",
        help="read configuration from CONFIG_FILE", metavar="CONFIG_FILE" )

    (options, args) = optionParser.parse_args()
    subControllerConfig = SubControllerConfig()

    if options.configFilename != None \
        and os.path.exists( options.configFilename ):
    
        configFile = file( options.configFilename, "r" )
        subControllerConfig = yaml.load( configFile )
        configFile.close()

    subController = SubController( subControllerConfig )
    while 1:
        subController.update()



    
