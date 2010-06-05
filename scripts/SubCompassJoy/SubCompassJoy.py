#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple joystick application for controlling the sub
#-------------------------------------------------------------------------------

import sys
import os.path
import shutil
import math
from optparse import OptionParser

import pygtk
pygtk.require('2.0')    # we want GTKv2
import gtk
import gobject
from playerc import *
import cv
import yaml

# Add common packages directory to path
sys.path.append( "../" )
from SubControllerConfig import SubControllerConfig

#-------------------------------------------------------------------------------
class MainWindow:
    
    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):
    
        self.config = config
        self.controlActive = False
        self.normalisedForwardSpeed = 0.0
        self.normalisedAngularSpeed = 0.0
        self.forwardSpeed = 0.0
        self.angularSpeed = 0.0
        
        self.connectToPlayer()
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) + "/SubCompassJoy.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgControlArea = builder.get_object( "dwgControlArea" )
        self.spinMaxForwardSpeed = builder.get_object( "spinMaxForwardSpeed" )
        self.spinMaxAngularSpeed = builder.get_object( "spinMaxAngularSpeed" )
        self.lblForwardSpeed = builder.get_object( "lblForwardSpeed" )
        self.lblAngularSpeed = builder.get_object( "lblAngularSpeed" )
        self.lblCompassAngle = builder.get_object( "lblCompassAngle" )

        self.spinMaxForwardSpeed.set_value( 0.5 )
        self.spinMaxAngularSpeed.set_value( 30.0 )

        (self.CONTROL_AREA_WIDTH, self.CONTROL_AREA_HEIGHT) = self.dwgControlArea.get_size_request()
        self.CONTROL_BOX_WIDTH = self.CONTROL_AREA_WIDTH
        self.HALF_CONTROL_BOX_WIDTH = self.CONTROL_BOX_WIDTH / 2.0
        self.DEAD_ZONE_WIDTH = self.CONTROL_AREA_WIDTH*0.0
        self.HALF_DEAD_ZONE_WIDTH = self.DEAD_ZONE_WIDTH / 2.0

        builder.connect_signals( self )
        
        self.window.show()

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
            
            # Try to also create one for position3d.1 if it exists
            self.otherPlayerPos3d = playerc_position3d( self.playerClient, 1 )
            if self.otherPlayerPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.otherPlayerPos3d = None
                
            # Try to connect to imu:0
            self.playerCompass = playerc_imu( self.playerClient, 0 )
            if self.playerCompass.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerCompass = None

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
    def updateNormalisedSpeeds( self, x, y ):

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

            self.normalisedAngularSpeed = x / MAX_DEFLECTION
            self.normalisedForwardSpeed = -y / MAX_DEFLECTION

    #---------------------------------------------------------------------------
    def onDwgControlAreaButtonPressEvent( self, widget, event ):
        
        if event.button == 1:
            self.updateNormalisedSpeeds( event.x, event.y )
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
           self.updateNormalisedSpeeds( event.x, event.y )
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
        if self.controlActive:
            widget.window.draw_line( graphicsContext, 
                centreX, centreY,
                int( centreX + self.normalisedAngularSpeed*self.HALF_CONTROL_BOX_WIDTH ),
                int( centreY - self.normalisedForwardSpeed*self.HALF_CONTROL_BOX_WIDTH ) )

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
    
        while 1:
            
            # Update the compass value if needed
            if self.playerCompass != None and self.playerClient.peek( 0 ):
                self.playerClient.read()
                
                #print "Data timestamp =", self.playerCompass.info.datatime
                newCompassAngle = self.playerCompass.pose.pyaw*180.0/math.pi
                self.lblCompassAngle.set_text( "{0:.2}".format( newCompassAngle ) )
                

            maxForwardSpeed = self.spinMaxForwardSpeed.get_value()
            maxAngularSpeed = self.spinMaxAngularSpeed.get_value()*math.pi/180.0

            if self.controlActive:
                print "controlActive = True"
                newForwardSpeed = self.normalisedForwardSpeed*maxForwardSpeed
                newAngularSpeed = -self.normalisedAngularSpeed*maxAngularSpeed
            else:
                print "controlActive = False"
                newForwardSpeed = 0.0
                newAngularSpeed = 0.0

            if newForwardSpeed != self.forwardSpeed \
                or newAngularSpeed != self.angularSpeed:

                # Send the new speed to player
                self.playerPos3d.set_velocity( newForwardSpeed, 0.0, 0.0, # x, y, z
                                               0.0, 0.0, newAngularSpeed, # roll, pitch, yaw
                                               0 )   # State
                print self.otherPlayerPos3d                            
                if self.otherPlayerPos3d != None:
                    self.otherPlayerPos3d.set_velocity( newForwardSpeed, 0.0, 0.0, # x, y, z
                                                        0.0, 0.0, newAngularSpeed, # roll, pitch, yaw
                                                        0 )   # State

                # Display the speeds
                self.lblForwardSpeed.set_text( "{0:.2}".format( newForwardSpeed ) )
                self.lblAngularSpeed.set_text( "{0:.2}".format( newAngularSpeed ) )
            
                # Store the speeds
                self.forwardSpeed = newForwardSpeed
                self.angularSpeed = newAngularSpeed
                
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
