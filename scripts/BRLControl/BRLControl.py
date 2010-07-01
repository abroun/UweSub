#! /usr/bin/python
#-------------------------------------------------------------------------------
# Control program for swimming around the BRL tank
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
from Maths.Vector2D import Vector2D, Normalise
from Steering.SteerToTarget import SteerToTarget
from RoBoardControl import ColourTracker

#-------------------------------------------------------------------------------
class SubControllerConfig( yaml.YAMLObject ):

    yaml_tag = u'!SubControllerConfig'

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

    FORWARD_SPEED = 0.5
    YAW_SPEED = 0.3
    SCREEN_RADIUS_OF_CLOSE_BUOY = 0.2
    
    def __init__( self ):
        self.robotType = self.ROBOT_TYPE_REAL

        self.playerServerAddress = self.PLAYER_SERVER_ADDRESS
        self.playerServerPort = self.PLAYER_SERVER_PORT

        self.trackedHue = self.TRACKED_HUE
        self.maxAbsHueDiff = self.MAX_ABS_HUE_DIFF
        self.trackedSaturation = self.TRACKED_SATURATION
        self.maxAbsSaturationDiff = self.MAX_ABS_SATURATION_DIFF
        self.trackedValue = self.TRACKED_VALUE
        self.maxAbsValueDiff = self.MAX_ABS_VALUE_DIFF

        self.forwardSpeed = self.FORWARD_SPEED
        self.yawSpeed = self.YAW_SPEED
        self.screenRadiusOfCloseBuoy = self.SCREEN_RADIUS_OF_CLOSE_BUOY

#-------------------------------------------------------------------------------
class SubLocator:

    def __init__( self, pos, heading ):
        self.pos = pos
        self.heading = heading

    def GetPosition( self ):
        return self.pos

    def GetHeading( self ):
        return self.heading

#-------------------------------------------------------------------------------
class MainWindow:
   
    PLAYER_SERVER_ADDRESS = 'localhost'
    PLAYER_SERVER_PORT = 6665

    SCALE_UP = 1.25
    SCALE_DOWN = 1.0 / SCALE_UP
    MIN_SCALE = 10.0
    MAX_SCALE = 1000000.0

    SUB_STATE_MOVING_TO_BUOY = "MovingToBuoy"
    SUB_STATE_MOVING_TO_GATE = "MovingToGate"

    LEFT = "Left"
    RIGHT = "Right"

    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):
    
        self.displayPixBuf = None
        self.lastCameraFrameTime = 0.0
        self.frameNumber = 0

        self.displayOriginX = 150
        self.displayOriginY = 200
        self.displayScale = 100
        self.draggingDisplay = False
        self.lastDragPos = None
        self.subPos = None
        self.subHeading = None
        self.subState = self.SUB_STATE_MOVING_TO_GATE

        self.robotType = config.robotType
        self.tracker = ColourTracker()
        self.tracker.setTrackedHue( config.trackedHue, config.maxAbsHueDiff )
        self.tracker.setTrackedSaturation( config.trackedSaturation, config.maxAbsSaturationDiff )
        self.tracker.setTrackedValue( config.trackedValue, config.maxAbsValueDiff )
        
        self.lastTurnDirection = self.LEFT
        self.forwardSpeed = config.forwardSpeed
        self.absYawSpeed = abs( config.yawSpeed )
        self.screenRadiusOfCloseBuoy = config.screenRadiusOfCloseBuoy

        self.connectToPlayer()

        # Get map
        # Get the position of the Buoy
        buoyPose = self.playerSim.get_pose2d( "Buoy" )
        if buoyPose[ 0 ] == 0:
            self.buoyPos = Vector2D( buoyPose[ 1 ], buoyPose[ 2 ] )
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

            self.leftGatePos = Vector2D( leftGateX, leftGateY )
            self.rightGatePos = Vector2D( rightGateX, rightGateY )
        else:
            print "Warning: Unable to get Gate pose"

        self.fixedLandmarks = [ self.buoyPos, self.leftGatePos, self.rightGatePos ]
        self.gateTargetPos = (self.leftGatePos + self.rightGatePos)/2.0 + Vector2D( -0.25, 0.0 )
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) 
            + "/BRLControl.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgDisplay = builder.get_object( "dwgDisplay" )
        self.dwgMap = builder.get_object( "dwgMap" )
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
    def onDwgMapExposeEvent( self, widget, event ):
        
        (windowWidth, windowHeight) = widget.window.get_size()

        originX = self.displayOriginX
        originY = self.displayOriginY
        scaleX = self.displayScale
        scaleY = -self.displayScale

        graphicsContext = widget.window.new_gc()
        graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 65535, 65535 ) )

        widget.window.draw_rectangle( graphicsContext, filled=True,
            x=0, y=0, width=windowWidth, height=windowHeight ) 
            
        # Draw the landmarks
        for fixedLandmark in self.fixedLandmarks:
            x = int( originX + scaleX*fixedLandmark.x )
            y = int( originY + scaleY*fixedLandmark.y )
            innerRadius = 0.05*scaleX
            outerRadius = 0.25*scaleX
            
            graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 0, 0 ) )
            self.drawCircle( widget.window, graphicsContext, x, y, innerRadius, filled = True )
            
            graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535/2, 65535/2, 65535/2 ) )
            self.drawCircle( widget.window, graphicsContext, x, y, outerRadius, filled = False )

        # Draw the AUV
        if self.subPos != None:
            graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 0, 0 ) )
            subRenderPos = ( originX + scaleX*self.subPos.x, originY + scaleY*self.subPos.y )
            self.drawCircle( widget.window, graphicsContext,
                subRenderPos[ 0 ], subRenderPos[ 1 ], 
                0.05*self.displayScale, filled=True )

            yaw = self.subHeading
            headingX = math.cos( yaw + math.pi/2.0 )*scaleX*0.10
            headingY = math.sin( yaw + math.pi/2.0 )*scaleY*0.10

            widget.window.draw_line( graphicsContext, 
                int( subRenderPos[ 0 ] ), int( subRenderPos[ 1 ] ),
                int( subRenderPos[ 0 ] + headingX ), int( subRenderPos[ 1 ] + headingY ) )
       
    #---------------------------------------------------------------------------
    def onDwgMapScrollEvent( self, widget, event = None ):
        if event.direction == gtk.gdk.SCROLL_UP: 
            self.displayScale *= self.SCALE_UP
        else: 
            self.displayScale *= self.SCALE_DOWN

        if self.displayScale < self.MIN_SCALE:
            self.displayScale = self.MIN_SCALE
        if self.displayScale > self.MAX_SCALE:
            self.displayScale = self.MAX_SCALE

        self.dwgMap.queue_draw()

    #---------------------------------------------------------------------------
    def onDwgMapButtonPressEvent( self, widget, event = None ):
        
        if event.button == 1:
            self.draggingDisplay = True
            self.lastDragPos = ( event.x, event.y )

    #---------------------------------------------------------------------------
    def onDwgMapButtonReleaseEvent( self, widget, event = None ):
        
        if event.button == 1:
            self.draggingDisplay = False

    #---------------------------------------------------------------------------
    def onDwgMapMotionNotifyEvent( self, widget, event = None ):
    
        if self.draggingDisplay == True:
            newDragPos = ( event.x, event.y )
    
            if newDragPos != self.lastDragPos:
                self.displayOriginX += newDragPos[ 0 ] - self.lastDragPos[ 0 ]
                self.displayOriginY += newDragPos[ 1 ] - self.lastDragPos[ 1 ]
                self.lastDragPos = newDragPos
                self.dwgMap.queue_draw()
     
    #---------------------------------------------------------------------------
    def drawCircle( self, drawable, graphicsContext, x, y, radius, filled ):
        topLeftX = int( x - radius )
        topLeftY = int( y - radius )
        width = height = int( radius * 2 )

        drawable.draw_arc( graphicsContext, 
            filled, topLeftX, topLeftY, width, height, 0, 360 * 64 )

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
                    processedFrameData = self.tracker.processFrame( rgbImage )
                    self.frame = rgbImage

                    # Get the submarine's pose
                    subPose = self.playerSim.get_pose2d( "Sub" )
                    subFound = ( subPose[ 0 ] == 0 )

                    if subFound:

                        self.subPos = Vector2D( subPose[ 1 ], subPose[ 2 ] )
                        self.subHeading = subPose[ 3 ]
                        
                        self.updateSubControl()
                    else:
                        print "Warning: Unable to get Sub pose"

                    # Display the image
                    self.displayPixBuf = gtk.gdk.pixbuf_new_from_data( 
                        processedFrameData, #rgbImage.tostring(), 
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
                    self.dwgMap.queue_draw()
                    self.lastCameraFrameTime = cameraFrameTime
                
            yield True
            
        yield False

    #---------------------------------------------------------------------------
    def updateSubControl( self ):
        
        ARRIVAL_DISTANCE = 0.1

        subLocator = SubLocator( self.subPos, self.subHeading )
        steerToTargetBehaviour = SteerToTarget( subLocator )

        if self.subState == self.SUB_STATE_MOVING_TO_BUOY:

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

                        halfRadius = radiusOfCloseBuoy / 2.0
                        if blobData.radius > halfRadius:
                            # Slow down as we approach the buoy
                            slowDownAmount = (blobData.radius - halfRadius)/halfRadius
                            forwardSpeed - (0.9*forwardSpeed)*slowDownAmount
                    else:
                        command = "Stay Still"
                        self.subState = self.SUB_STATE_MOVING_TO_GATE

                print "Buoy Visible at ( " + str( blobData.centreX ) + ", " + str( blobData.centreY ) + " ) - " + command

            else:
                print "Can't see buoy - turning " + self.lastTurnDirection.lower()

                # Turn to search for the buoy
                if self.lastTurnDirection == self.LEFT:
                    yawSpeed = self.absYawSpeed
                else:
                    yawSpeed = -self.absYawSpeed

            # Steer the AUV
            self.applySteeringResult( ( forwardSpeed, yawSpeed ) )

        else: # self.subState == self.SUB_STATE_MOVING_TO_GATE

            # Move to gate target pos

            # Check to see if we have arrived
            curPos = subLocator.GetPosition()
            distanceToTargetPos = ( self.gateTargetPos - curPos ).Length()
            if distanceToTargetPos < ARRIVAL_DISTANCE:
                self.subState = self.SUB_STATE_MOVING_TO_BUOY
            else:

                # Use reactive steering behaviours to try and get to the target position
                steeringResult = None #self.avoidWallBehaviour.update()
                if steeringResult == None:
                    steerToTargetBehaviour.setTargetPos( self.gateTargetPos )
                    steeringResult = steerToTargetBehaviour.update()
                self.applySteeringResult( steeringResult )

    #---------------------------------------------------------------------------
    def applySteeringResult( self, steeringResult ):
        """Sends a steering result in the form of a forward speed and heading speed
           down to the robot"""
        if steeringResult != None:
            self.playerPos3d.set_velocity( 
                steeringResult[ 0 ], 0.0, 0.0, # x, y, z
                0.0, 0.0, steeringResult[ 1 ], # roll, pitch, yaw
                0 )   # State
            #self.lastSteeringResult = steeringResult

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