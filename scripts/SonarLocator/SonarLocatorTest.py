#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple app to test the SonarLocator module
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

from SonarLocator import SonarLocator

# Add common packages directory to path
sys.path.append( "../" )
from SubControllerConfig import SubControllerConfig

#-------------------------------------------------------------------------------
class MainWindow:
    
    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):
    
        self.config = config
        
        self.sonarPixBuf = None
        self.lastSonarFrameTime = 0.0

        self.connectToPlayer()
        self.sonarLocator = SonarLocator( self.playerCompass, self.playerSonar, config )
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) 
            + "/SonarLocatorTest.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgDisplay = builder.get_object( "dwgDisplay" )
        self.textentry = builder.get_object( "entry1")        
        builder.connect_signals( self )
        
        self.window.show()

        updateLoop = self.update()
        gobject.idle_add( updateLoop.next )

        # Slightly crappy way to start up the joystick...
        #subJoyWindow = SubJoy.MainWindow( config )
        #subJoyWindow.main()
    
    #---------------------------------------------------------------------------
    def connectToPlayer( self ):
        
        try:
            # Create a client object to connect to Player
            self.playerClient = playerc_client( None, 
                self.config.playerServerAddress, self.config.playerServerPort )
            
            # Connect it
            if self.playerClient.connect() != 0:
                raise Exception( playerc_error_str() )
            
            # Create a proxy for the compass
            self.playerCompass = playerc_imu( self.playerClient, 0 )
            if self.playerCompass.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise Exception( playerc_error_str() )
            
            # And for the sonar
            self.playerSonar = playerc_micronsonar( self.playerClient, 0 )
            if self.playerSonar.subscribe( PLAYERC_OPEN_MODE ) != 0:
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
    def onMainWinDestroy( self, widget, data = None ):  
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
    def onBtnTestClicked( self, widget, data = None ):
        self.playerSpeech.say( self.textentry.get_text() )

    #---------------------------------------------------------------------------
    def onDwgDisplayExposeEvent( self, widget, event ):
    
        if self.sonarPixBuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget,
                self.sonarPixBuf.get_width(), self.sonarPixBuf.get_height() )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                self.sonarPixBuf, srcX, srcY, 
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
    def isNewSonarFrameAvailable( self ):
        if self.playerSonar == None:
            return False
        else:
            return self.lastSonarFrameTime != self.playerSonar.info.datatime

    #---------------------------------------------------------------------------
    def update( self ):
    
        while 1:
            
            self.sonarLocator.update()
            
            if self.playerClient.peek( 0 ):
                self.playerClient.read()

                if self.isNewSonarFrameAvailable():
                    sonarFrameTime = self.playerSonar.info.datatime

                    # Give the image to OpenCV as a very inefficient way to
                    # convert to RGB
                    grayImage = cv.CreateImageHeader( ( self.playerSonar.width, self.playerSonar.height ), cv.IPL_DEPTH_8U, 1 )       
                    cv.SetData( grayImage, self.playerSonar.image[:self.playerSonar.image_count], self.playerSonar.width )
        
                    rgbImage = cv.CreateImage( ( self.playerSonar.width, self.playerSonar.height ), cv.IPL_DEPTH_8U, 3 )
                    cv.CvtColor( grayImage, rgbImage, cv.CV_GRAY2RGB )

                    #zoom = self.spinZoom.get_value()
                    #if zoom != 1.0:
                    #    scaledImage = cv.CreateImage( 
                    #        ( int( rgbImage.width*zoom ), 
                    #         int ( rgbImage.height*zoom ) ), 
                    #        rgbImage.depth, rgbImage.nChannels )
                   # 
                    #    cv.Resize( rgbImage, scaledImage )
                    #    rgbImage = scaledImage
        
                    # Display the image
                    self.displayPixBuf = gtk.gdk.pixbuf_new_from_data( 
                        rgbImage.tostring(), 
                        gtk.gdk.COLORSPACE_RGB,
                        False,
                        rgbImage.depth,
                        rgbImage.width,
                        rgbImage.height,
                        rgbImage.width*rgbImage.nChannels )

                    # Resize the drawing area if necessary
                    if self.dwgDisplay.get_size_request() != ( rgbImage.width, rgbImage.height ):
                        self.dwgDisplay.set_size_request( rgbImage.width, rgbImage.height )

                    self.dwgDisplay.queue_draw()
                    
                    self.lastSonarFrameTime = sonarFrameTime
                
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
        configFile.close()

    mainWindow = MainWindow( subControllerConfig )
    mainWindow.main()