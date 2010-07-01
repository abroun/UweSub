#! /usr/bin/python
#-------------------------------------------------------------------------------
# Attempts to stress out the submarine and wireless connection by subscribing
# to all of the Player interfaces
#-------------------------------------------------------------------------------

import sys
import os.path
import shutil
import math
from optparse import OptionParser

import pygtk
pygtk.require('2.0')
import gtk
import gobject
from playerc import *
import cv
import yaml

# Add common packages directory to path
sys.path.append( "../" )
from SubControllerConfig import SubControllerConfig
import SubJoy

#-------------------------------------------------------------------------------
class MainWindow:
    
    IMAGE_SCALE = 1.0
    
    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):
    
        self.config = config
        self.recording = False
        self.outputSequence = None
        self.outputFilename = None
        self.sonarPixBuf = None
        self.mainCameraPixBuf = None
        self.otherCameraPixBuf = None
        self.lastSonarFrameTime = 0.0
        self.lastMainCameraFrameTime = 0.0
        self.lastOtherCameraFrameTime = 0.0
        self.frameNumber = 0
        self.testTime = 0.0

        self.connectToPlayer()
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) 
            + "/StressTest.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgCam1 = builder.get_object( "dwgCam1" )
        self.dwgCam2 = builder.get_object( "dwgCam2" )
        self.dwgSonar = builder.get_object( "dwgSonar" )
        builder.connect_signals( self )
        
        self.window.show()

        updateLoop = self.update()
        gobject.idle_add( updateLoop.next )
        
        self.scanSector = 0;
        self.startSonarScan();
        
        # Slightly crappy way to start up the joystick...
        subJoyWindow = SubJoy.MainWindow( config )
        subJoyWindow.main()

    #---------------------------------------------------------------------------
    def startSonarScan( self ):
        # Configure the sonar
        self.playerSonar.set_config( 
            3, 300, 0.3 )
             
        # Start the scan
        self.playerSonar.scan( (self.scanSector*90.0)*math.pi/180.0, 
            (((self.scanSector+2)%4)*90.0)*math.pi/180.0 )
            
        self.scanSector = (self.scanSector+1)%4

    #---------------------------------------------------------------------------
    def connectToPlayer( self ):
        
        try:
            # Create a client object to connect to Player
            self.playerClient = playerc_client( None, 
                self.config.playerServerAddress, self.config.playerServerPort )
            
            # Connect it
            if self.playerClient.connect() != 0:
                raise Exception( playerc_error_str() )

            # Create a proxy for micronsonar:0
            self.playerSonar = playerc_micronsonar( self.playerClient, 0 )
            if self.playerSonar.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise Exception( playerc_error_str() )
            
            # Create a proxy for camera:0
            self.playerMainCamera = playerc_camera( self.playerClient, 1 )
            if self.playerMainCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise Exception( playerc_error_str() )
            
            # Create a proxy for camera:1 if it exists
            self.playerOtherCamera = playerc_camera( self.playerClient, 2 )
            if self.playerOtherCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerOtherCamera = None
                
            # Create a proxy for position3d.0
            self.playerPos3d = playerc_position3d( self.playerClient, 0 )
            if self.playerPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
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
    def onWinMainDestroy( self, widget, data = None ):  
        gtk.main_quit()
        
    #---------------------------------------------------------------------------   
    def main( self ):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()
        
    #---------------------------------------------------------------------------   
    def ShowErrorMessage( self, msg ):

        dialog = gtk.MessageDialog( parent=None, 
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            type=gtk.MESSAGE_ERROR, 
            buttons=gtk.BUTTONS_OK, 
            message_format=msg )
                
        dialog.set_title( "Error" )
        dialog.run()
        dialog.destroy()

    #---------------------------------------------------------------------------
    def onDwgSonarExposeEvent( self, widget, event ):
    
        self.exposeDwg( widget, event, self.sonarPixBuf )
        
    #---------------------------------------------------------------------------
    def onDwgCam1ExposeEvent( self, widget, event ):
    
        self.exposeDwg( widget, event, self.mainCameraPixBuf )
        
    #---------------------------------------------------------------------------
    def onDwgCam2ExposeEvent( self, widget, event ):
    
        self.exposeDwg( widget, event, self.otherCameraPixBuf )
        
    #---------------------------------------------------------------------------
    def exposeDwg( self, widget, event, dwgPixbuf ):
    
        if dwgPixbuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget,
                dwgPixbuf.get_width(), dwgPixbuf.get_height() )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                dwgPixbuf, srcX, srcY, 
                imgRect.x, imgRect.y, imgRect.width, imgRect.height )


    #---------------------------------------------------------------------------
    def getImageRectangleInWidget( self, widget, imageWidth, imageHeight ):
        
        # Centre the image inside the widget
        widgetX, widgetY, widgetWidth, widgetHeight = widget.get_allocation()
        
        imgRect = gtk.gdk.Rectangle( 0, 0, widgetWidth, widgetHeight )
        
        if widgetWidth > imageWidth:
            imgRect.x = (widgetWidth - imageWidth) / 2
            imgRect.width = imageWidth
            
        if widgetHeight > imageHeight:
            imgRect.y = (widgetHeight - imageHeight) / 2
            imgRect.height = imageHeight
        
        return imgRect

    #---------------------------------------------------------------------------
    def updateMainCameraImage( self ):
        
        if self.lastMainCameraFrameTime != self.playerMainCamera.info.datatime:
            cameraFrameTime = self.playerMainCamera.info.datatime

            if self.playerMainCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                self.playerMainCamera.decompress()
    
            if self.playerMainCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                print "Error: Unable to decompress frame"
                sys.exit( -1 )

            # Give the image to OpenCV as a very inefficient way to
            # save it as a jpeg
            rgbImage = cv.CreateImageHeader( ( self.playerMainCamera.width, self.playerMainCamera.height ), cv.IPL_DEPTH_8U, 3 )       
            cv.SetData( rgbImage, self.playerMainCamera.image[:self.playerMainCamera.image_count], self.playerMainCamera.width*3 )

            # Display the image
            self.mainCameraPixBuf = gtk.gdk.pixbuf_new_from_data( 
                rgbImage.tostring(), 
                gtk.gdk.COLORSPACE_RGB,
                False,
                rgbImage.depth,
                rgbImage.width,
                rgbImage.height,
                rgbImage.width*rgbImage.nChannels )

            # Resize the drawing area if necessary
            if self.dwgCam1.get_size_request() != ( rgbImage.width, rgbImage.height ):
                self.dwgCam1.set_size_request( rgbImage.width, rgbImage.height )

            self.dwgCam1.queue_draw()
            self.lastMainCameraFrameTime = cameraFrameTime
    
    #---------------------------------------------------------------------------
    def updateOtherCameraImage( self ):
        
        if self.playerOtherCamera == None:
            return
        
        if self.lastOtherCameraFrameTime != self.playerOtherCamera.info.datatime:
            cameraFrameTime = self.playerOtherCamera.info.datatime

            if self.playerOtherCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                self.playerOtherCamera.decompress()
    
            if self.playerOtherCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                print "Error: Unable to decompress frame"
                sys.exit( -1 )

            # Give the image to OpenCV as a very inefficient way to
            # save it as a jpeg
            rgbImage = cv.CreateImageHeader( ( self.playerOtherCamera.width, self.playerOtherCamera.height ), cv.IPL_DEPTH_8U, 3 )       
            cv.SetData( rgbImage, self.playerOtherCamera.image[:self.playerOtherCamera.image_count], self.playerOtherCamera.width*3 )

            # Display the image
            self.otherCameraPixBuf = gtk.gdk.pixbuf_new_from_data( 
                rgbImage.tostring(), 
                gtk.gdk.COLORSPACE_RGB,
                False,
                rgbImage.depth,
                rgbImage.width,
                rgbImage.height,
                rgbImage.width*rgbImage.nChannels )

            # Resize the drawing area if necessary
            if self.dwgCam2.get_size_request() != ( rgbImage.width, rgbImage.height ):
                self.dwgCam2.set_size_request( rgbImage.width, rgbImage.height )

            self.dwgCam2.queue_draw()
            self.lastOtherCameraFrameTime = cameraFrameTime
    
    #---------------------------------------------------------------------------
    def updateSonarImage( self ):
        
        if self.playerSonar == None:
            return
        else:
            if self.lastSonarFrameTime != self.playerSonar.info.datatime:
        
                sonarFrameTime = self.playerSonar.info.datatime

                # Give the image to OpenCV as a very inefficient way to
                # convert to RGB
                grayImage = cv.CreateImageHeader( ( self.playerSonar.width, self.playerSonar.height ), cv.IPL_DEPTH_8U, 1 )       
                cv.SetData( grayImage, self.playerSonar.image[:self.playerSonar.image_count], self.playerSonar.width )
    
                rgbImage = cv.CreateImage( ( self.playerSonar.width, self.playerSonar.height ), cv.IPL_DEPTH_8U, 3 )
                cv.CvtColor( grayImage, rgbImage, cv.CV_GRAY2RGB )

                # Display the image
                self.sonarPixBuf = gtk.gdk.pixbuf_new_from_data( 
                    rgbImage.tostring(), 
                    gtk.gdk.COLORSPACE_RGB,
                    False,
                    rgbImage.depth,
                    rgbImage.width,
                    rgbImage.height,
                    rgbImage.width*rgbImage.nChannels )

                # Resize the drawing area if necessary
                if self.dwgSonar.get_size_request() != ( rgbImage.width, rgbImage.height ):
                    self.dwgSonar.set_size_request( rgbImage.width, rgbImage.height )

                self.dwgSonar.queue_draw()
                
                # Also write out image
                #bgrImage = cv.CreateImage( ( self.playerSonar.width, self.playerSonar.height ), cv.IPL_DEPTH_8U, 3 )
                #cv.CvtColor( grayImage, bgrImage, cv.CV_GRAY2BGR )
                #cv.SaveImage( "sonar.png", bgrImage )
                
                self.startSonarScan()
                self.lastSonarFrameTime = sonarFrameTime


    #---------------------------------------------------------------------------
    def update( self ):
    
        while 1:
            
            # Send the new speed to player
            forwardSpeed = math.sin( self.testTime )
            self.playerPos3d.set_velocity( 
                        forwardSpeed, 0.0, 0.0, # x, y, z
                        0.0, 0.0, 0.0, # roll, pitch, yaw
                        0 )   # State
        
            self.testTime += 0.0001
            
            if self.playerClient.peek( 0 ):
                self.playerClient.read()
                
                self.updateMainCameraImage()
                self.updateOtherCameraImage()
                self.updateSonarImage()
                
            yield True
            
        yield False

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
        subControllerConfig.addUnsetVariables()
        configFile.close()

    mainWindow = MainWindow( subControllerConfig )
    mainWindow.main()
