#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple app for recording simulation test sequences
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
            + "/TestSequenceRecorder.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgDisplay = builder.get_object( "dwgDisplay" )
        self.tbxOutputFile = builder.get_object( "tbxOutputFile" )
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

            # Create a proxy for simulation:0
            self.playerSim = playerc_simulation( self.playerClient, 0 )
            if self.playerSim.subscribe( PLAYERC_OPEN_MODE ) != 0:
                print "Unable to connect to simulayion:0. Assuming that we're talking to a real robot"
                self.playerSim = None
            
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

        if not self.recording and self.playerSim != None:

            self.outputFilename = self.tbxOutputFile.get_text()
            outputDir = os.path.dirname( self.outputFilename )

            # Check that the output directory exists
            if not os.path.exists( outputDir ):

                self.ShowErrorMessage( "Can't find the output directory" )
                return

            # Work out where we're going to store the images and check if
            # it's ok to delete anything which may already be there
            self.outputImageDir = os.path.splitext( self.outputFilename )[ 0 ] + "_images"
            if os.path.exists( self.outputImageDir ): 

                msgString = "The directory where the images will be stored - " \
                    "{0} - already exists. Is it ok to overwrite it?".format( self.outputImageDir )

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
                        shutil.rmtree( self.outputImageDir )
                    except Exception as e:
                        self.ShowErrorMessage( "Error when deleting image directory - " + str( e ) )
                        return
            
            # Create the image directory
            os.mkdir( self.outputImageDir )

            # Start recording
            self.outputSequence = TestSequence.TestSequence()

            # Get the position of the Buoy
            buoyPose = self.playerSim.get_pose2d( "Buoy" )
            if buoyPose[ 0 ] == 0:
                self.outputSequence.addFixedEntity(
                    TestSequence.FixedEntityData( "Buoy", buoyPose[ 1 ], buoyPose[ 2 ] ) )
            else:
                print "Warning: Unable to get Buoy pose"

            # Get the position of the Gate
            gatePose = self.playerSim.get_pose2d( "Gate" )
            if gatePose[ 0 ] == 0:

                GATE_WIDTH = 0.9
                HALF_GATE_WIDTH = GATE_WIDTH / 2.0

                # We can only deal with point features so enter the 
                # gate posts as two separate entities
                sinAngle = math.sin( gatePose[ 3 ] )
                cosAngle = math.cos( gatePose[ 3 ] )

                leftGateX = gatePose[ 1 ] - HALF_GATE_WIDTH*cosAngle
                leftGateY = gatePose[ 2 ] - HALF_GATE_WIDTH*sinAngle
                rightGateX = gatePose[ 1 ] + HALF_GATE_WIDTH*cosAngle
                rightGateY = gatePose[ 2 ] + HALF_GATE_WIDTH*sinAngle

                self.outputSequence.addFixedEntity(
                    TestSequence.FixedEntityData( "LeftGatePost", leftGateX, leftGateY ) )
                self.outputSequence.addFixedEntity(
                    TestSequence.FixedEntityData( "RightGatePost", rightGateX, rightGateY ) )
            else:
                print "Warning: Unable to get Gate pose"

            self.frameNumber = 0
            self.recording = True

    #---------------------------------------------------------------------------
    def onBtnStopRecordingClicked( self, widget, data = None ):

        if self.recording:
            outputFile = file( self.outputFilename, "w" )
            yaml.dump( self.outputSequence, outputFile )
            outputFile.close()
            self.recording = False

    #---------------------------------------------------------------------------
    def onBtnOutputFileClicked( self, widget, data = None ):

        filter = gtk.FileFilter()
        filter.add_pattern( "*.yaml" )
        filter.set_name( "Sequence Files" )

        dialog = gtk.FileChooserDialog(
            title="Choose Output File",
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT) )

        dialog.set_current_folder( "../../data/Sequences" )
        dialog.add_filter( filter )
        dialog.set_filter( filter )
        result = dialog.run()

        if result == gtk.RESPONSE_ACCEPT:
            filename = dialog.get_filename()
            if os.path.splitext( filename )[ 1 ] == "":
                filename += ".yaml"

            self.tbxOutputFile.set_text( filename )

        dialog.destroy()

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
                    cameraFrameTime = self.playerCamera.info.datatime

                    if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                        self.playerCamera.decompress()
            
                    if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
                        print "Error: Unable to decompress frame"
                        sys.exit( -1 )

                    # Give the image to OpenCV as a very inefficient way to
                    # save it as a jpeg
                    rgbImage = cv.CreateImageHeader( ( self.playerCamera.width, self.playerCamera.height ), cv.IPL_DEPTH_8U, 3 )       
                    cv.SetData( rgbImage, self.playerCamera.image[:self.playerCamera.image_count], self.playerCamera.width*3 )
        
                    if self.recording:
                        # Get the submarine's pose
                        subPose = self.playerSim.get_pose2d( "Sub" )
                        subFound = ( subPose[ 0 ] == 0 )

                        if subFound:

                            # Save the current image
                            imageFilename = "{0}/frame_{1:06}_{2}.jpeg".format( 
                                self.outputImageDir, self.frameNumber, cameraFrameTime )
                            relativeImageFilename = os.path.relpath( imageFilename, os.path.dirname( self.outputFilename ) )

                            bgrImage = cv.CreateImage( ( rgbImage.width, rgbImage.height ), cv.IPL_DEPTH_8U, 3 )
                            cv.CvtColor( rgbImage, bgrImage, cv.CV_RGB2BGR )
                            cv.SaveImage( imageFilename, bgrImage )

                            # Record the frame
                            self.outputSequence.addFrame(
                                TestSequence.FrameData( subPose[ 1 ], subPose[ 2 ], subPose[ 3 ],
                                    cameraFrameTime, relativeImageFilename ) )

                            self.frameNumber += 1
                        else:
                            print "Warning: Unable to get Sub pose"

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
                    self.lastCameraFrameTime = cameraFrameTime
                
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
