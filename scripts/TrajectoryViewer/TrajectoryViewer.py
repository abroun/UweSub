#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple joystick application for controlling the sub
#-------------------------------------------------------------------------------

import sys
import os.path
import math

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import cv

import RoBoardControl

# Add common packages directory to path
sys.path.append( "../" )
import SubJoy
import TestSequence
from Maths.Vector2D import Vector2D, Normalise
from TrajectoryEstimator import TrajectoryEstimator

#-------------------------------------------------------------------------------
class MainWindow:

    SCALE_UP = 1.25
    SCALE_DOWN = 1.0 / SCALE_UP
    MIN_SCALE = 10.0
    MAX_SCALE = 1000000.0
    

    #---------------------------------------------------------------------------
    def __init__( self ):
        
        self.cameraDisplayPixBuf = None
        self.settingFrame = False

        # Load in a test sequence
        self.testSequenceDir = "../../data/Sequences"
        self.testSequence = TestSequence.loadSequenceFromFile( self.testSequenceDir + "/BRLSimTest.yaml" )
        self.numFrames = len( self.testSequence.frames )

        self.displayOriginX = 150
        self.displayOriginY = 200
        self.displayScale = 100
        self.draggingDisplay = False
        self.lastDragPos = None

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

        self.estimateTrajectoryGradientDescent()

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

        originX = self.displayOriginX
        originY = self.displayOriginY
        scaleX = self.displayScale
        scaleY = -self.displayScale

        numPoints = self.curFrameIdx - 1
        pointList = [ ( int( originX + scaleX*self.testSequence.frames[ i ].subX ),
            int( originY + scaleY*self.testSequence.frames[ i ].subY ) ) for i in range( self.curFrameIdx ) ]

        

        estimatedTrajectoryPointList = \
            [ ( int( originX + scaleX*self.estimator.poseGuesses[ i ][ 0 ] ),
            int( originY + scaleY*self.estimator.poseGuesses[ i ][ 1 ] ) ) \
            for i in range( self.curFrameIdx ) ]

        


        graphicsContext = widget.window.new_gc()
        graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 65535, 65535 ) )

        widget.window.draw_rectangle( graphicsContext, filled=True,
            x=0, y=0, width=windowWidth, height=windowHeight ) 

        if numPoints > 0:
            graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 0, 0 ) )
            graphicsContext.set_line_attributes( 2, gtk.gdk.LINE_SOLID,
                gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_BEVEL )
            widget.window.draw_points( graphicsContext, pointList ) 

            lastPoint = pointList[ -1 ]
            self.drawCircle( widget.window, graphicsContext,
                lastPoint[ 0 ], lastPoint[ 1 ], 0.05*self.displayScale, filled=True )

            yaw = self.testSequence.frames[ self.curFrameIdx - 1 ].subYaw
            headingX = math.cos( yaw + math.pi/2.0 )*scaleX*0.10
            headingY = math.sin( yaw + math.pi/2.0 )*scaleY*0.10

            widget.window.draw_line( graphicsContext, 
                lastPoint[ 0 ], lastPoint[ 1 ],
                lastPoint[ 0 ] + headingX, lastPoint[ 1 ] + headingY )

            
            graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 0, 0 ) )
            graphicsContext.set_line_attributes( 2, gtk.gdk.LINE_SOLID,
                gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_BEVEL )
            widget.window.draw_points( graphicsContext, estimatedTrajectoryPointList ) 

            lastEstimnatedPoint = estimatedTrajectoryPointList[ -1 ]
            self.drawCircle( widget.window, graphicsContext,
                lastEstimnatedPoint[ 0 ], lastEstimnatedPoint[ 1 ], 
                0.05*self.displayScale, filled=True )

            yaw = self.estimator.poseGuesses[ self.curFrameIdx - 1 ][ 2 ]
            headingX = math.cos( yaw + math.pi/2.0 )*scaleX*0.10
            headingY = math.sin( yaw + math.pi/2.0 )*scaleY*0.10

            widget.window.draw_line( graphicsContext, 
                lastEstimnatedPoint[ 0 ], lastEstimnatedPoint[ 1 ],
                lastEstimnatedPoint[ 0 ] + headingX, lastEstimnatedPoint[ 1 ] + headingY )

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
    def onDwgTrajectoryDisplayScrollEvent( self, widget, event = None ):
        if event.direction == gtk.gdk.SCROLL_UP: 
            self.displayScale *= self.SCALE_UP
        else: 
            self.displayScale *= self.SCALE_DOWN

        if self.displayScale < self.MIN_SCALE:
            self.displayScale = self.MIN_SCALE
        if self.displayScale > self.MAX_SCALE:
            self.displayScale = self.MAX_SCALE

        self.dwgTrajectoryDisplay.queue_draw()

    #---------------------------------------------------------------------------
    def onDwgTrajectoryDisplayButtonPressEvent( self, widget, event = None ):
        
        if event.button == 1:
            self.draggingDisplay = True
            self.lastDragPos = ( event.x, event.y )

    #---------------------------------------------------------------------------
    def onDwgTrajectoryDisplayButtonReleaseEvent( self, widget, event = None ):
        
        if event.button == 1:
            self.draggingDisplay = False

    #---------------------------------------------------------------------------
    def onDwgTrajectoryDisplayMotionNotifyEvent( self, widget, event = None ):
    
        if self.draggingDisplay == True:
            newDragPos = ( event.x, event.y )
    
            if newDragPos != self.lastDragPos:
                self.displayOriginX += newDragPos[ 0 ] - self.lastDragPos[ 0 ]
                self.displayOriginY += newDragPos[ 1 ] - self.lastDragPos[ 1 ]
                self.lastDragPos = newDragPos
                self.dwgTrajectoryDisplay.queue_draw()

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

    #---------------------------------------------------------------------------
    def estimateTrajectory( self ):

        CAMERA_FOV = 44.0*math.pi/180.0
        HALF_CAMERA_FOV = CAMERA_FOV / 2.0
        COS_OF_HALF_CAMERA_FOV = math.cos( HALF_CAMERA_FOV )
        CAMERA_WIDTH = 320.0
        HALF_CAMERA_WIDTH = CAMERA_WIDTH / 2.0
        CAMERA_HEIGHT = 240.0
        HALF_CAMERA_HEIGHT = CAMERA_HEIGHT / 2.0
        FOCAL_DISTANCE = CAMERA_WIDTH / ( 2.0*math.tan( CAMERA_FOV / 2.0 ) )
        FOCAL_HYP_X = math.sqrt( FOCAL_DISTANCE*FOCAL_DISTANCE + HALF_CAMERA_WIDTH*HALF_CAMERA_WIDTH )

        # Create camera parameters
        #cameraParams = [ FOCAL_DISTANCE, 0.0, CAMERA_WIDTH / 2.0,
        #                 0.0, FOCAL_DISTANCE, CAMERA_HEIGHT / 2.0,
        #                 0.0, 0.0, 1.0 ]

        cameraParams = [ 
            FOCAL_DISTANCE, # fu 
            CAMERA_WIDTH / 2.0, # u0
            CAMERA_HEIGHT / 2.0,    # v0
            CAMERA_HEIGHT / CAMERA_WIDTH, # Ratio to get from width to height
            0.0 ]   # Skew

        # Create initial guesses for the camera poses and landmark positions
        motionStruct = [0] * 6 * self.numFrames  # Place camera guesses at the origin

        for entity in self.testSequence.fixedEntities:
            motionStruct.extend( [ entity.x, entity.y, 0.0 ] )

        # Repeat camera rotation guesses as quaternions
        initialRotations = [ 1.0, 0.0, 0.0, 0.0 ] * self.numFrames

        # For each frame work out where the landmarks are projected
        numEntities = len( self.testSequence.fixedEntities )
        landmarkPoints = []
        landmarkVisibility = [0] * self.numFrames * numEntities

        for entityIdx in range( numEntities ):
            entity = self.testSequence.fixedEntities[ entityIdx ]

            for frameIdx in range( self.numFrames ):
                frameData = self.testSequence.frames[ frameIdx ]
                subHeading = Vector2D( -math.sin( frameData.subYaw ), 
                    math.cos( frameData.subYaw ) )
                dirToEntity = Normalise( 
                    Vector2D( entity.x - frameData.subX, entity.y - frameData.subY ) )

                cosOfAngleToEntity = subHeading.Dot( dirToEntity )
                if cosOfAngleToEntity > COS_OF_HALF_CAMERA_FOV:
                    # Entity is visible in this frame
                    landmarkVisibility[ entityIdx * self.numFrames + frameIdx ] = 1
                    
                    subXAxis = Vector2D( subHeading.y, -subHeading.x )
                    if subXAxis.Dot( dirToEntity ) > 0.0:
                        entityPixelX = HALF_CAMERA_WIDTH + cosOfAngleToEntity*FOCAL_HYP_X
                    else:
                        entityPixelX = HALF_CAMERA_WIDTH - cosOfAngleToEntity*FOCAL_HYP_X

                    landmarkPoints.extend( [ entityPixelX, HALF_CAMERA_HEIGHT ] )
        
        # Use bundle adjustment to estimate camera positions
        print len( landmarkPoints )
        poseResults = RoBoardControl.bundleAdjustment( 
            self.numFrames, numEntities, len( landmarkPoints ) / 2,
            motionStruct, initialRotations, 
            landmarkPoints, landmarkVisibility, cameraParams )
        print poseResults

    #---------------------------------------------------------------------------
    def bearingToFeature( self, subX, subY, subYaw, featureX, featureY ):
        return math.atan2( featureY - subY, featureX - subX ) - subYaw

    #---------------------------------------------------------------------------
    def estimateTrajectoryGradientDescent( self ):

        CAMERA_FOV = 44.0*math.pi/180.0
        HALF_CAMERA_FOV = CAMERA_FOV / 2.0
        COS_OF_HALF_CAMERA_FOV = math.cos( HALF_CAMERA_FOV )
        CAMERA_WIDTH = 320.0
        HALF_CAMERA_WIDTH = CAMERA_WIDTH / 2.0
        CAMERA_HEIGHT = 240.0
        HALF_CAMERA_HEIGHT = CAMERA_HEIGHT / 2.0
        FOCAL_DISTANCE = CAMERA_WIDTH / ( 2.0*math.tan( CAMERA_FOV / 2.0 ) )
        FOCAL_HYP_X = math.sqrt( FOCAL_DISTANCE*FOCAL_DISTANCE + HALF_CAMERA_WIDTH*HALF_CAMERA_WIDTH )

        # Initial guesses for position and orientation  
        poseGuesses = []
        for poseIdx in range( self.numFrames ):
            poseGuesses.append( [ 0.0, 0.0, 0.0 ] )

        # For each frame work out where the landmarks are projected
        numEntities = len( self.testSequence.fixedEntities )
        landmarkPositions = [(e.x, e.y) for e in self.testSequence.fixedEntities]
        landmarkBearings = []
        landmarkVisibility = []

        for frameIdx in range( self.numFrames ):
            frameData = self.testSequence.frames[ frameIdx ]

            bearingArray = []
            visibilityArray = []

            for entityIdx in range( numEntities ):
                entity = self.testSequence.fixedEntities[ entityIdx ]

                bearing = self.bearingToFeature( 
                    frameData.subX, frameData.subY, frameData.subYaw,
                    entity.x, entity.y )
                bearingArray.append( bearing )

                # Entity is visible in this frame
                visibilityArray.append( math.cos( bearing ) > COS_OF_HALF_CAMERA_FOV )
            
            landmarkBearings.append( bearingArray )
            landmarkVisibility.append( visibilityArray )

        # Use bundle adjustment to estimate camera positions
        self.estimator = TrajectoryEstimator()
        totalError = self.estimator.estimateTrajectory( 
            poseGuesses, landmarkPositions, 
            landmarkBearings, landmarkVisibility )

        print "Average Error =", totalError / self.numFrames

#-------------------------------------------------------------------------------
if __name__ == "__main__":

    mainWindow = MainWindow()
    mainWindow.main()