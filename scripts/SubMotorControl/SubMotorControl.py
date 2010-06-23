#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple application for controlling the sub's motors
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
import time
import pygame
from pygame import locals

# Add common packages directory to path
sys.path.append( "../" )
from SubControllerConfig import SubControllerConfig

#-------------------------------------------------------------------------------
class MainWindow:
    
    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):
    
        self.config = config
        self.controlActive = False
        self.normalisedJoystickDeflection = 0.0
        self.joystickHeading = 0.0  # Anti-clockwise heading with 0 pointing forward
        self.forwardSpeed = 0.0
        self.angularSpeed = 0.0
        
        self.oldFrontMotorValue = 0.0
        self.oldBackMotorValue = 0.0
        
        self.connectToPlayer()
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) + "/SubMotorControl.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgControlArea = builder.get_object( "dwgControlArea" )
        self.vscaleLeftMotor = builder.get_object( "vscaleLeftMotor" )
        self.vscaleRightMotor = builder.get_object( "vscaleRightMotor" )
        self.vscaleFrontMotor = builder.get_object( "vscaleFrontMotor" )
        self.vscaleBackMotor = builder.get_object( "vscaleBackMotor" )
        self.chkLinkVerticalMotors = builder.get_object( "chkLinkVerticalMotors" )

        (self.CONTROL_AREA_WIDTH, self.CONTROL_AREA_HEIGHT) = self.dwgControlArea.get_size_request()
        self.CONTROL_BOX_WIDTH = self.CONTROL_AREA_WIDTH*0.95
        self.HALF_CONTROL_BOX_WIDTH = self.CONTROL_BOX_WIDTH / 2.0
        self.DEAD_ZONE_WIDTH = self.CONTROL_AREA_WIDTH*0.20
        self.HALF_DEAD_ZONE_WIDTH = self.DEAD_ZONE_WIDTH / 2.0

        builder.connect_signals( self )
        
        self.window.show()

        pygame.init()
        pygame.joystick.init() # main joystick device system


        try:
            self.j = pygame.joystick.Joystick(0) # create a joystick instance
            self.j.init() # init instance
            print 'Enabled joystick: ' + self.j.get_name()
        except pygame.error:
            print 'no joystick found.'


        updateLoop = self.update()
        gobject.idle_add( updateLoop.next )
    
    #---------------------------------------------------------------------------
    def connectToPlayer( self ):
        
        try:
            # Create a client object to connect to Player
            self.playerClient = playerc_client( None, 
                self.config.playerServerAddress, self.config.playerServerPort )
            
            # Connect it
            if self.playerClient.connect() != 0:
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
            self.showErrorMessage( "Exception when connecting to Player - " + str( e ) )
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
    def showErrorMessage( self, msg ):

        dialog = gtk.MessageDialog( parent=None, 
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            type=gtk.MESSAGE_ERROR, 
            buttons=gtk.BUTTONS_OK, 
            message_format=msg )
                
        dialog.set_title( "Error" )
        dialog.run()
        dialog.destroy()

    #---------------------------------------------------------------------------
    def updateLeftRightMotorSpeeds( self, x, y ):

        MAX_DEFLECTION = self.HALF_CONTROL_BOX_WIDTH

        if self.controlActive:
    
            # Offset the input
            x -= self.HALF_CONTROL_BOX_WIDTH
            y -= self.HALF_CONTROL_BOX_WIDTH

            # Constrain the input
            if x > MAX_DEFLECTION:
                x = MAX_DEFLECTION
            elif x < -MAX_DEFLECTION:
                x = -MAX_DEFLECTION

            if y > MAX_DEFLECTION:
                y = MAX_DEFLECTION
            elif y < -MAX_DEFLECTION:
                y = -MAX_DEFLECTION

            # Apply the dead zone
            if x >= -self.HALF_DEAD_ZONE_WIDTH \
                and x <= self.HALF_DEAD_ZONE_WIDTH:
                x = 0.0
            if y >= -self.HALF_DEAD_ZONE_WIDTH \
                and y <= self.HALF_DEAD_ZONE_WIDTH:
                y = 0.0

            self.joystickHeading = math.atan2( -x, -y )
            
            normalisedX = x / MAX_DEFLECTION
            normalisedY = y / MAX_DEFLECTION
            self.normalisedJoystickDeflection = math.sqrt( normalisedX*normalisedX + normalisedY*normalisedY )
            if self.normalisedJoystickDeflection > 1.0:
                self.normalisedJoystickDeflection = 1.0
    
    #---------------------------------------------------------------------------
    def onVscaleFrontMotorValueChanged( self, widget, event = None ):
    
        newValue = widget.get_value()
        if self.oldFrontMotorValue != newValue:
            self.oldFrontMotorValue = newValue
            
            if self.chkLinkVerticalMotors.get_active():
                self.vscaleBackMotor.set_value( newValue )
               
    #---------------------------------------------------------------------------
    def onVscaleBackMotorValueChanged( self, widget, event = None ):
    
        newValue = widget.get_value()
        if self.oldBackMotorValue != newValue:
            self.oldBackMotorValue = newValue
            
            if self.chkLinkVerticalMotors.get_active():
                self.vscaleFrontMotor.set_value( newValue )
    
    #---------------------------------------------------------------------------
    def onChkLinkVerticalMotorsToggled( self, widget, event = None ):
        
        if self.chkLinkVerticalMotors.get_active():
                self.vscaleBackMotor.set_value( self.vscaleFrontMotor.get_value() )
    
    #---------------------------------------------------------------------------
    def onDwgControlAreaButtonPressEvent( self, widget, event ):
        
        if event.button == 1:
            self.updateLeftRightMotorSpeeds( event.x, event.y )
            self.controlActive = True

            self.dwgControlArea.queue_draw()

    #---------------------------------------------------------------------------
    def onDwgControlAreaButtonReleaseEvent( self, widget, event ):
        
        if event.button == 1:
            self.controlActive = False
            self.dwgControlArea.queue_draw()

    #---------------------------------------------------------------------------
    def onDwgControlAreaMotionNotifyEvent( self, widget, event ):

        if self.controlActive:
            self.updateLeftRightMotorSpeeds( event.x, event.y )
            self.dwgControlArea.queue_draw()

    #---------------------------------------------------------------------------
    def onDwgControlAreaExposeEvent( self, widget, event ):
    
        FILLED = True

        innerCircleRadius = (self.CONTROL_AREA_WIDTH/2.0) * 0.01 
        centreX = int( self.CONTROL_AREA_WIDTH/2 )
        centreY = int( self.CONTROL_AREA_HEIGHT/2 )
            
        imgRect = self.getImageRectangleInWidget( widget )
            
        imgOffsetX = imgRect.x
        imgOffsetY = imgRect.y
            
        # Get the total area that needs to be redrawn
        imgRect = imgRect.intersect( event.area )
    
        # Draw the background
        graphicsContext = widget.window.new_gc()
        graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 65535, 65535 ) )

        widget.window.draw_rectangle( graphicsContext, filled=True,
            x=imgRect.x, y=imgRect.y, width=imgRect.width, height=imgRect.height ) 

        # Draw the control area
        graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 0, 0 ) )
        self.drawCircle( widget.window, graphicsContext, 
            centreX, centreY, innerCircleRadius, filled=True )
        widget.window.draw_rectangle( graphicsContext, filled=False,
            x=int( centreX - self.HALF_CONTROL_BOX_WIDTH ), 
            y=int( centreY - self.HALF_CONTROL_BOX_WIDTH ),
            width=int( self.CONTROL_BOX_WIDTH ), 
            height=int( self.CONTROL_BOX_WIDTH ) )
        widget.window.draw_rectangle( graphicsContext, filled=False,
            x=int( centreX - self.HALF_DEAD_ZONE_WIDTH ), 
            y=int( centreY - self.HALF_DEAD_ZONE_WIDTH ),
            width=int( self.DEAD_ZONE_WIDTH ), 
            height=int( self.DEAD_ZONE_WIDTH ) )

        # Draw the control arrow if needed
        if self.normalisedJoystickDeflection > 0.0:
            widget.window.draw_line( graphicsContext, 
                centreX, centreY,
                int( centreX - math.sin( self.joystickHeading )*self.HALF_CONTROL_BOX_WIDTH*self.normalisedJoystickDeflection ),
                int( centreY - math.cos( self.joystickHeading )*self.HALF_CONTROL_BOX_WIDTH*self.normalisedJoystickDeflection ) )

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
    def update( self ):
    
        MAX_DEFLECTION = self.HALF_CONTROL_BOX_WIDTH
        MAX_UPDATES_PER_SECOND = 30.0
        TIME_BETWEEN_UPDATES = 1.0 / MAX_UPDATES_PER_SECOND
        DIVE_CHANGE = 1.0 / 500.0
        
        zeroPosPose = player_pose3d_t()
        velocityPose = player_pose3d_t()
        lastTime = time.time()
    
        while 1:
            
            for e in pygame.event.get(): # iterate over event stack
               
                if e.type == pygame.locals.JOYAXISMOTION: # 7
                    x , y = self.j.get_axis(0), self.j.get_axis(1)
                    #print 'x and y : ' + str(x) +' , '+ str(y)
                    
                    # Apply the dead zone
                    if x >= -self.HALF_DEAD_ZONE_WIDTH/MAX_DEFLECTION \
                        and x <= self.HALF_DEAD_ZONE_WIDTH/MAX_DEFLECTION:
                        x = 0.0
                    if y >= -self.HALF_DEAD_ZONE_WIDTH/MAX_DEFLECTION \
                        and y <= self.HALF_DEAD_ZONE_WIDTH/MAX_DEFLECTION:
                        y = 0.0
                    
                    self.joystickHeading = math.atan2( -x, -y )
            
                    normalisedX = x
                    normalisedY = y
                    self.normalisedJoystickDeflection = math.sqrt( normalisedX*normalisedX + normalisedY*normalisedY )
                    if self.normalisedJoystickDeflection > 1.0:
                        self.normalisedJoystickDeflection = 1.0
                        
                    self.dwgControlArea.queue_draw()
                    
                    # Vertical control
                    z = self.j.get_axis(4)
                    if abs( z ) > 0.15:
                        self.chkLinkVerticalMotors.set_active( True )
                    
                        if z < 0.0:
                            self.vscaleFrontMotor.set_value(
                                self.vscaleFrontMotor.get_value() - DIVE_CHANGE )
                        else:
                            self.vscaleFrontMotor.set_value(
                                self.vscaleFrontMotor.get_value() + DIVE_CHANGE )
                
            #print self.normalisedJoystickDeflection
            
            #if not self.controlActive:
            #    self.normalisedJoystickDeflection = 0.0

            if self.normalisedJoystickDeflection > 0.0:
                forwardComponent = math.cos( self.joystickHeading )*self.normalisedJoystickDeflection
                turnComponent = math.sin( self.joystickHeading )*self.normalisedJoystickDeflection
            
                leftMotorSpeed = forwardComponent - turnComponent
                leftMotorSpeed = max( -1.0, min( leftMotorSpeed, 1.0 ) )
                rightMotorSpeed = forwardComponent + turnComponent
                rightMotorSpeed = max( -1.0, min( rightMotorSpeed, 1.0 ) )
            else:
                leftMotorSpeed = 0.0
                rightMotorSpeed = 0.0
            
            self.vscaleLeftMotor.set_value( leftMotorSpeed )
            self.vscaleRightMotor.set_value( rightMotorSpeed )

            curTime = time.time()
            if curTime - lastTime > TIME_BETWEEN_UPDATES:
                     
                frontMotorSpeed = self.vscaleFrontMotor.get_value()
                backMotorSpeed = self.vscaleBackMotor.get_value()
            
                print "Sending ", leftMotorSpeed, rightMotorSpeed, frontMotorSpeed, backMotorSpeed
            
                velocityPose.px = leftMotorSpeed
                velocityPose.py = rightMotorSpeed
                velocityPose.proll = frontMotorSpeed
                velocityPose.ppitch = backMotorSpeed
            
                self.playerPos3d.set_pose_with_vel( zeroPosPose, velocityPose )
                    
                lastTime = curTime            
                
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
