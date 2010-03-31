#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple app for recording simulation test sequences
#-------------------------------------------------------------------------------

import sys
import os.path
import shutil

import pygtk
pygtk.require('2.0')
import gtk
import gobject
from playerc import *
import cv

#-------------------------------------------------------------------------------
class MainWindow:
   
    PLAYER_SERVER_ADDRESS = 'localhost'
    PLAYER_SERVER_PORT = 6665

    #---------------------------------------------------------------------------
    def __init__( self ):
    
        self.recording = False
        self.displayPixBuf = None
        self.lastCameraFrameTime = 0.0

        self.connectToPlayer()
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( "TestSequenceRecorder.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgDisplay = builder.get_object( "dwgDisplay" )
        self.tbxOutputFile = builder.get_object( "tbxOutputFile" )
        builder.connect_signals( self )
        
        self.window.show()

        updateLoop = self.update()
        gobject.idle_add( updateLoop.next )
    
    #---------------------------------------------------------------------------
    def connectToPlayer( self ):
        
        try:
            # Create a client object to connect to Player
            self.playerClient = playerc_client( None, 
                self.PLAYER_SERVER_ADDRESS, self.PLAYER_SERVER_PORT )
            
            # Connect it
            if self.playerClient.connect() != 0:
                raise Exception( playerc_error_str() )

            # Create a proxy for simulation:0
            self.playerSim = playerc_simulation( self.playerClient, 0 )
            if self.playerSim.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise Exception( playerc_error_str() )
            
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
    def onBtnStartRecordingClicked( self, widget, data = None ):

        if not self.recording:

            outputFilename = self.tbxOutputFile.get_text()
            outputDir = os.path.dirname( outputFilename )

            # Check that the output directory exists
            if not os.path.exists( outputDir ):

                self.ShowErrorMessage( "Can't find the output directory" )
                return

            # Work out where we're going to store the images and check if
            # it's ok to delete anything which may already be there
            self.imageDir = os.path.splitext( outputFilename )[ 0 ] + "_images"
            if os.path.exists( self.imageDir ): 

                msgString = "The directory where the images will be stored - " \
                    "{0} - already exists. Is it ok to overwrite it?"

                dialog = gtk.MessageDialog( parent=None, 
                    flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    type=gtk.MESSAGE_WARNING, 
                    buttons=gtk.BUTTONS_YES_NO, 
                    message_format=msgString)
                
                dialog.set_title("Warning")
                result = dialog.run()
                dialog.destroy()

                if result == gtk.RESPONSE_NO:
                    return
                else:
                    try:
                        shutil.rmtree( self.imageDir )
                    except Exception as e:
                        self.ShowErrorMessage( "Error when deleting image directory - " + str( e ) )
                        return
            
            # Create the image directory
            os.mkdir( self.imageDir )

            # Start recording
            self.outputFile = open( outputFilename, "w" )
            self.recording = True

    #---------------------------------------------------------------------------
    def onBtnStopRecordingClicked( self, widget, data = None ):

        if self.recording:
            self.outputFile.close()
            self.recording = False

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
        return self.lastCameraFrameTime != self.playerCamera.info.datatime

    #---------------------------------------------------------------------------
    def update( self ):
    
        while 1:
            if self.playerClient.peek( 0 ):
                self.playerClient.read()

                if self.isNewFrameAvailable():
                    self.lastCameraFrameTime = self.playerCamera.info.datatime

                    if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                        self.playerCamera.decompress()
            
                    if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                        print "Error: Unable to decompress frame"
                        sys.exit( -1 )

                    # Give the image to OpenCV as a very inefficient way to
                    # save it as a jpeg
                    rgbImage = cv.CreateImageHeader( ( self.playerCamera.width, self.playerCamera.height ), cv.IPL_DEPTH_8U, 3 )       
                    cv.SetData( rgbImage, self.playerCamera.image[:self.playerCamera.image_count], self.playerCamera.width*3 )
        
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
                
            yield True
            
        yield False

#-------------------------------------------------------------------------------
if __name__ == "__main__":

    mainWindow = MainWindow()
    mainWindow.main()