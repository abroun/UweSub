#! /usr/bin/python

#-------------------------------------------------------------------------------
# Control program for submarine
#-------------------------------------------------------------------------------

import cv
from playerc import *
import Profiling
#from ColourTracker import ColourTracker
from RoBoardControl import ColourTracker

#-------------------------------------------------------------------------------
class SubController:

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

    #---------------------------------------------------------------------------
    def __init__( self, robotType = ROBOT_TYPE_REAL, 
                  playerServerAddress = PLAYER_SERVER_ADDRESS, 
                  playerServerPort = PLAYER_SERVER_PORT ):

        self.robotType = robotType
        self.tracker = ColourTracker()
        self.tracker.setTrackedHue( self.TRACKED_HUE, self.MAX_ABS_HUE_DIFF )
        self.tracker.setTrackedSaturation( self.TRACKED_SATURATION, self.MAX_ABS_SATURATION_DIFF )
        self.tracker.setTrackedValue( self.TRACKED_VALUE, self.MAX_ABS_VALUE_DIFF )
        
        self.frame = None
        self.frameWidth = 320
        self.frameHeight = 240
        
        # Create a client object
        self.playerClient = playerc_client( None, playerServerAddress, playerServerPort )
        # Connect it
        if self.playerClient.connect() != 0:
            raise playerc_error_str()

        self.playerPos3d = None
        if self.robotType == self.ROBOT_TYPE_SIM:
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
                     
            blobData = self.tracker.getBlobData()
            if blobData.visible:
                print "Buoy Visible at ( " + str( blobData.centreX ) + ", " + str( blobData.centreY ) + " )"
            else:
                print "Can't see blob"
        
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
    subController = SubController()
    while 1:
        subController.update()



    
