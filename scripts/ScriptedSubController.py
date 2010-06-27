#! /usr/bin/python

#-------------------------------------------------------------------------------
# Control program for submarine that executes a script
#-------------------------------------------------------------------------------

import os
from optparse import OptionParser

import cv
import yaml
from playerc import *
import Profiling

#from ColourTracker import ColourTracker
from RoBoardControl import ColourTracker
from SubControllerConfig import SubControllerConfig

#-------------------------------------------------------------------------------
class ScriptedSubController:

    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):

        self.config = config
        
        # Create a client object
        self.playerClient = playerc_client( None, 
            config.playerServerAddress, config.playerServerPort )
        # Connect it
        if self.playerClient.connect() != 0:
            raise playerc_error_str()

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
    def connectToPlayer( self ):
        
        try:
            # Create a client object to connect to Player
            self.playerClient = playerc_client( None, 
                self.config.playerServerAddress, self.config.playerServerPort )
            
            # Connect it
            if self.playerClient.connect() != 0:
                raise Exception( playerc_error_str() )

            # Create proxies
            self.playerPos3d = playerc_position3d( self.playerClient, 0 )
            if self.playerPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise Exception( playerc_error_str() )
                
            # Try to connect to imu:0
            self.playerCompass = playerc_imu( self.playerClient, 0 )
            if self.playerCompass.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerCompass = None
            
            self.playerDepthSensor = playerc_position1d( self.playerClient, 0 )
            if self.playerDepthSensor.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerDepthSensor = None
            
            # And for the camera
            self.playerCamera = playerc_camera( self.playerClient, 0 )
            if self.playerCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise Exception( playerc_error_str() )

            if self.playerClient.datamode( PLAYERC_DATAMODE_PULL ) != 0:
                raise Exception( playerc_error_str() )
        
            if self.playerClient.set_replace_rule( -1, -1, PLAYER_MSGTYPE_DATA, -1, 1 ) != 0:
                raise Exception( playerc_error_str() )
        except Exception as e:
            self.ShowErrorMessage( "Exception when connecting to Player - " + str( e ) )
            sys.exit( -1 )
    
        print "Connected to Player!"

            
    #---------------------------------------------------------------------------
    #@Profiling.printTiming
    def getImage( self ):
        
        self.lastCameraFrameTime = self.playerCamera.info.datatime

        if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
            self.playerCamera.decompress()
            
        if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
            print( "Error: Unable to decompress frame" );
            return None
       
        cvImage = cv.CreateImageHeader( ( self.playerCamera.width, self.playerCamera.height ), cv.IPL_DEPTH_8U, 3 )       
        cv.SetData( cvImage, self.playerCamera.image[:self.playerCamera.image_count], self.playerCamera.width*3 )
        
        return cvImage
        
    #---------------------------------------------------------------------------
    def update( self ):
        newFrameAvailable = False
    
        if self.playerClient.peek( 0 ):
            self.playerClient.read()

            if self.isNewFrameAvailable():
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
    def isNewFrameAvailable( self ):
        return self.lastCameraFrameTime != self.playerCamera.info.datatime

    #---------------------------------------------------------------------------
    @Profiling.printTiming
    def getAndProcessFrame( self ):
        
        self.frame = self.getImage()
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



    
