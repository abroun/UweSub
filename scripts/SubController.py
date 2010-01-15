#! /usr/bin/python

#-------------------------------------------------------------------------------
# Control program for submarine
#-------------------------------------------------------------------------------

import cv
from playerc import *
import Profiling

import array
im_array = array.array('B') #array of unsigned byte


ROBOT_TYPE_REAL = "Real"
ROBOT_TYPE_SIM = "Sim"

robotType = ROBOT_TYPE_REAL

testString = ""
for i in range( 320*240 ):
    testString = testString + chr(255)
    testString = testString + chr(0)
    testString = testString + chr(0)

@Profiling.printTiming
def getImage( playerClient, playerCamera, frameNum ):
    playerClient.read()
    if playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
        playerCamera.decompress()
        
    if playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
        print( "Error: Unable to decompress frame" );
        return
   
    #im_array.fromstring(playerCamera.image[:playerCamera.image_count])
    #print playerCamera.image
       
    cvIMage = None
    
    if robotType == ROBOT_TYPE_REAL:
        cvImage = cv.CreateImageHeader( ( playerCamera.width, playerCamera.height ), cv.IPL_DEPTH_8U, 3 )
        
        src = playerCamera.image[:playerCamera.image_count]
        #dst = ""
        #skip = False
        #for a in src:
        #    if not skip:
        #        dst = dst + a + a + a
        #    skip = not skip
        
        cv.SetData( cvImage, src, playerCamera.width*3 )
    else:
        cvImage = cv.CreateImageHeader( ( 256, 256 ), cv.IPL_DEPTH_8U, 3 )
        cv.SetData( cvImage, playerCamera.image[:playerCamera.image_count], 256*3 )
        #cv.CvtColor( cvImage, cvImage, cv.CV_RGB2BGR )
    
    cv.SaveImage( "test_output.ppm", cvImage )
        
    
    #playerCamera.save( "output/img_" + str( frameNum ) + ".ppm" )
    
def imageCallback( data ):
    print "Got Data"

# Create a client object
playerClient = playerc_client( None, 'localhost', 6665 )
# Connect it
if playerClient.connect() != 0:
    raise playerc_error_str()

playerPos3d = None
if robotType == ROBOT_TYPE_SIM:
    # Create a proxy for position3d:0
    playerPos3d = playerc_position3d( playerClient, 0 )
    if playerPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
        raise playerc_error_str()
        
playerCamera = playerc_camera( playerClient, 0 )
if playerCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
    raise playerc_error_str()

if playerClient.datamode( PLAYERC_DATAMODE_PULL ) != 0:
    raise playerc_error_str()
    
if playerClient.set_replace_rule( -1, -1, PLAYER_MSGTYPE_DATA, -1, 1 ) != 0:
    raise playerc_error_str()
    
print "Connected to Player!"



#cvImage = cv.CreateImageHeader( ( 320, 240 ), cv.IPL_DEPTH_8U, 3 )
#cv.SetData( cvImage, 

#while True:
#playerPos3d.set_velocity( 3.0, 0.0, 0.0, # x, y, z
#                    0.0, 0.0, 0.3, # roll, pitch, yaw
#                    0 )   # State

frameNum = 0
while True:
    if playerClient.peek( 0 ):
        getImage( playerClient, playerCamera, frameNum )
        frameNum = frameNum + 1
    #print frameNum

# Clean up
playerCamera.unsubscribe()
if playerPos3d != None:
    playerPos3d.unsubscribe()
playerClient.disconnect()


    