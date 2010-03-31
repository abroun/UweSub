#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple joystick application for controlling the sub
#-------------------------------------------------------------------------------

import sys
import os.path

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import cv

# Add common packages directory to path
sys.path.append( "../" )
import SubJoy
import TestSequence

#-------------------------------------------------------------------------------
class MainWindow:

    #---------------------------------------------------------------------------
    def __init__( self ):
        
        self.cameraDisplayPixBuf = None
        self.settingFrame = False

        # Load in a test sequence
        self.testSequenceDir = "../../data/Sequences"
        self.testSequence = TestSequence.loadSequenceFromFile( self.testSequenceDir + "/BRLSimTest.yaml" )
        self.numFrames = len( self.testSequence.frames )

        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) + "/TrajectoryViewer.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgTrajectoryDisplay = builder.get_object( "dwgTrajectoryDisplay" )
        self.dwgCameraDisplay = builder.get_object( "dwgCameraDisplay" )
        self.tbxFrameNumber = builder.get_object( "tbxFrameNumber" )
        self.lblNumFrames = builder.get_object( "lblNumFrames" )
        self.lblNumFrames.set_text( "/" + str( self.numFrames ) )

        builder.connect_signals( self )
        
        self.setCurFrameIdx( 0 )
        self.window.show()

    #---------------------------------------------------------------------------
    def onWinMainDestroy( self, widget, data = None ):  
        gtk.main_quit()
        
    #---------------------------------------------------------------------------   
    def main( self ):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()
        
    #---------------------------------------------------------------------------
    def onDwgTrajectoryDisplayExposeEvent( self, widget, event ):

        (windowWidth, windowHeight) = widget.window.get_size()

        originX = 150
        originY = 200
        scaleX = 100
        scaleY = -100
        numPoints = self.curFrameIdx - 1
        pointList = [ ( int( originX + scaleX*self.testSequence.frames[ i ].subX ),
            int( originY + scaleY*self.testSequence.frames[ i ].subY ) ) for i in range( self.curFrameIdx ) ]

        graphicsContext = widget.window.new_gc()
        graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 65535, 65535 ) )

        widget.window.draw_rectangle( graphicsContext, filled=True,
            x=0, y=0, width=windowWidth, height=windowHeight ) 

        graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 0, 0 ) )
        if numPoints > 0:
            widget.window.draw_points( graphicsContext, pointList ) 

    #---------------------------------------------------------------------------
    def onDwgCameraDisplayExposeEvent( self, widget, event ):
    
        if self.cameraDisplayPixBuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                self.cameraDisplayPixBuf, srcX, srcY, 
                imgRect.x, imgRect.y, imgRect.width, imgRect.height )

    #---------------------------------------------------------------------------
    def onBtnPrevFrameClicked( self, widget, data = None ):
        self.setCurFrameIdx( self.curFrameIdx - 1 )

    #---------------------------------------------------------------------------
    def onBtnNextFrameClicked( self, widget, data = None ):
        self.setCurFrameIdx( self.curFrameIdx + 1 )

    #---------------------------------------------------------------------------
    def onTbxFrameNumberFocusOut( self, widget, data = None ):
        try:
            self.setCurFrameIdx( int( self.tbxFrameNumber.get_text() ) - 1 )
        except:
            pass    # Catch errors that may occur whilst parsing an integer

    #---------------------------------------------------------------------------
    def onTbxFrameNumberKeyPressed( self, widget, keyPressEvent ):
        if gtk.gdk.keyval_name( keyPressEvent.keyval ) == "Return":
            self.onTbxFrameNumberFocusOut( widget )

    #---------------------------------------------------------------------------
    def drawCircle( self, drawable, graphicsContext, x, y, radius, filled ):
        topLeftX = int( x - radius )
        topLeftY = int( y - radius )
        width = height = int( radius * 2 )

        drawable.draw_arc( graphicsContext, 
            filled, topLeftX, topLeftY, width, height, 0, 360 * 64 )

    #---------------------------------------------------------------------------
    def getImageRectangleInWidget( self, widget ):
        
        # Centre the image inside the widget
        widgetX, widgetY, widgetWidth, widgetHeight = widget.get_allocation()
        
        imgRect = gtk.gdk.Rectangle( 0, 0, widgetWidth, widgetHeight )
        (requestedWidth, requestedHeight) = widget.get_size_request()
        
        if widgetWidth > requestedWidth:
            imgRect.x = (widgetWidth - requestedWidth) / 2
            imgRect.width = requestedWidth
            
        if widgetHeight > requestedHeight:
            imgRect.y = (widgetHeight - requestedHeight) / 2
            imgRect.height = requestedHeight
        
        return imgRect

    #---------------------------------------------------------------------------
    def setCurFrameIdx( self, frameIdx ):

        if self.settingFrame:
            raise "NotReentrant"

        self.settingFrame = True

        # Clip the frame index to a valid number
        if frameIdx < 0:
            frameIdx = 0
        elif frameIdx >= self.numFrames:
            frameIdx = self.numFrames - 1

        # Display the selected frame
        self.curFrameIdx = frameIdx

        imageFilename = self.testSequenceDir \
            + "/" + self.testSequence.frames[ self.curFrameIdx ].imageFilename
        bgrImage = cv.LoadImage( imageFilename )
        self.curFrameImage = cv.CreateImage( ( bgrImage.width, bgrImage.height ), cv.IPL_DEPTH_8U, 3 )
        cv.CvtColor( bgrImage, self.curFrameImage, cv.CV_BGR2RGB )

        self.cameraDisplayPixBuf = gtk.gdk.pixbuf_new_from_data( 
            self.curFrameImage.tostring(), 
            gtk.gdk.COLORSPACE_RGB,
            False,
            self.curFrameImage.depth,
            self.curFrameImage.width,
            self.curFrameImage.height,
            self.curFrameImage.width*self.curFrameImage.nChannels )

        # Update the text-box that displays the current frame number
        self.tbxFrameNumber.set_text( str( self.curFrameIdx + 1 ) )

        # Resize the drawing area if necessary
        if self.dwgCameraDisplay.get_size_request() != ( self.curFrameImage.width, self.curFrameImage.height ):
            self.dwgCameraDisplay.set_size_request( self.curFrameImage.width, self.curFrameImage.height )
        
        # Redraw the frames
        self.dwgTrajectoryDisplay.queue_draw()
        self.dwgCameraDisplay.queue_draw()
        
        self.settingFrame = False

#-------------------------------------------------------------------------------
if __name__ == "__main__":

    mainWindow = MainWindow()
    mainWindow.main()