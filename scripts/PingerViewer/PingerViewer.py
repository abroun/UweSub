#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple app talking to the pinger driver
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
import SubJoy
import TestSequence
from SubControllerConfig import SubControllerConfig

#-------------------------------------------------------------------------------
class MainWindow:
    
    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):
    
        self.config = config
        self.recording = False
        self.outputSequence = None
        self.outputFilename = None
        self.displayPixBuf = None
        self.lastCameraFrameTime = 0.0
        self.frameNumber = 0

        self.connectToPlayer()
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) 
            + "/PingerViewer.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgDisplay = builder.get_object( "dwgDisplay" )
        self.textentry1 = builder.get_object( "entry1") 
        self.textentry2 = builder.get_object( "entry2")       
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
            
            # dspic interface 
            self.playerPIC = playerc_dspic( self.playerClient, 0 )
            if self.playerPIC.subscribe( PLAYERC_OPEN_MODE ) != 0:
                print "Unable to connect to dsPIC:0"
                raise Exception( playerc_error_str() )
            
            # And for the camera
            self.playerCamera = None
            #self.playerCamera = playerc_camera( self.playerClient, 0 )
            #if self.playerCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
            #    raise Exception( playerc_error_str() )

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
        self.playerPIC.say( self.textentry1.get_text() )

    #---------------------------------------------------------------------------
    def onDwgDisplayExposeEvent( self, widget, event ):
    
        if self.displayPixBuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget,
                self.displayPixBuf.get_width(), self.displayPixBuf.get_height() )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                self.displayPixBuf, srcX, srcY, 
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
    def isNewFrameAvailable( self ):
        if self.playerCamera == None:
            return False
        else:
            return self.lastCameraFrameTime != self.playerCamera.info.datatime

    #---------------------------------------------------------------------------
    def update( self ):
    
        while 1:
            if self.playerClient.peek( 0 ):
                self.playerClient.read()

                if (self.playerPIC.msgtype ==0) or (self.playerPIC.msgtype==1) or (self.playerPIC.msgtype==2):
                    self.textentry2.set_text(str(self.playerPIC.reading))
                elif (self.playerPIC.msgtype==4):
                    self.textentry2.set_text(str(self.playerPIC.distance))
                elif (self.playerPIC.msgtype==5):
                    self.textentry2.set_text(str(self.playerPIC.intensity))
                
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
