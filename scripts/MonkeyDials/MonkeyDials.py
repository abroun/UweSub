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
pygtk.require('2.0')	# we want GTKv2
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
        self.normalisedLinearSpeed = 0.0
        self.normalisedAngularSpeed = 0.0
	    self.normalisedDepthSpeed = 0.0
	    self.depthSpeed = 0.0
        self.linearSpeed = 0.0
        self.angularSpeed = 0.0
        
        self.connectToPlayer()
    
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) + "/MonkeyDials.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.viewZ = builder.get_object( "viewZ" )
        self.viewXY = builder.get_object( "viewXY" )
	    self.spinMaxDepthSpeed = builder.get_object( "spinMaxDepthSpeed" )
        self.spinMaxLinearSpeed = builder.get_object( "spinMaxLinearSpeed" )
        self.spinMaxAngularSpeed = builder.get_object( "spinMaxAngularSpeed" )
        self.depthSpeed = builder.get_object( "scaleDepthSpeed" )
        self.linearSpeed = builder.get_object( "scaleLinearSpeed" )
        self.angularSpeed = builder.get_object( "scaleAngularSpeed" )

        self.spinMaxDepthSpeed.set_value( 2.0 )
        self.spinMaxLinearSpeed.set_value( 0.5 )
        self.spinMaxAngularSpeed.set_value( 30.0 )

    	self.BAR_WIDTH = 100
        self.CONTROL_BAR_WIDTH = self.BAR_WIDTH*0.95
	    self.HALF_CONTROL_BAR_WIDTH = self.CONTROL_BAR_WIDTH / 2.0
        self.DEAD_ZONE_WIDTH = self.BAR_WIDTH*0.0
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

            if self.playerClient.datamode( PLAYERC_DATAMODE_PULL ) != 0:
                raise Exception( playerc_error_str() )
        
            if self.playerClient.set_replace_rule( -1, -1, PLAYER_MSGTYPE_DATA, -1, 1 ) != 0:
                raise Exception( playerc_error_str() )
        except Exception as e:
            self.showErrorMessage( "Exception when connecting to Player - " + str( e ) )
            sys.exit( -1 )
    
        print "Connected to Player!"

#---------------------------------------------------------------------------
   # The program exits when the window is closed
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
    def updateNormalisedZ( self, z ):
	# z -> depth speed
	
	MAX_DEFLECTION = self.CONTROL_BAR_WIDTH

        if self.controlActive:
    
            # Offset the input
            z -= MAX_DEFLECTION

            # Constrain the input
            if z > MAX_DEFLECTION:
                z = MAX_DEFLECTION
            elif z < -MAX_DEFLECTION:
                z = -MAX_DEFLECTION

            
            # Apply the dead zone
	    if z >= -self.DEAD_ZONE_WIDTH \
                and z <= self.DEAD_ZONE_WIDTH:
                z = 0.0

            self.normalisedDepthSpeed = -z / MAX_DEFLECTION
   
#---------------------------------------------------------------------------
    def updateNormalisedX( self, x ):
	# x -> linear speed
	
	MAX_DEFLECTION = self.HALF_CONTROL_BAR_WIDTH

        if self.controlActive:
    
            # Offset the input
            x -= MAX_DEFLECTION

            # Constrain the input
            if x > MAX_DEFLECTION:
                x = MAX_DEFLECTION
            elif x < -MAX_DEFLECTION:
                x = -MAX_DEFLECTION

            # Apply the dead zone
            if x >= -self.HALF_DEAD_ZONE_WIDTH \
                and x <= self.HALF_DEAD_ZONE_WIDTH:
                x = 0.0

            self.normalisedLinearSpeed = x / MAX_DEFLECTION

#---------------------------------------------------------------------------
    def updateNormalisedY( self, y ):
	# y -> angular speed
	
	MAX_DEFLECTION = self.HALF_CONTROL_BAR_WIDTH

        if self.controlActive:
    
            # Offset the input
            y -= MAX_DEFLECTION

            # Constrain the input
            if y > MAX_DEFLECTION:
                y = MAX_DEFLECTION
            elif y < -MAX_DEFLECTION:
                y = -MAX_DEFLECTION

            # Apply the dead zone
            if y >= -self.HALF_DEAD_ZONE_WIDTH \
                and x <= self.HALF_DEAD_ZONE_WIDTH:
                y = 0.0

            self.normalisedAngularSpeed = y / MAX_DEFLECTION

#---------------------------------------------------------------------------
    def onDepthSpeedControlButtonPressEvent( self, widget, event ):
        
        if event.button == 1:
            self.updateNormalisedZ( event.z )
            self.controlActive = True
            self.viewZ.queue_draw()

#---------------------------------------------------------------------------
    def onDepthSpeedControlButtonReleaseEvent( self, widget, event ):
        
        if event.button == 1:
            self.controlActive = False
            self.viewZ.queue_draw()
   
#---------------------------------------------------------------------------
    def onLinearSpeedControlButtonPressEvent( self, widget, event ):
        
        if event.button == 1:
            self.updateNormalisedZ( event.x )
            self.controlActive = True
            self.viewXY.queue_draw()

#---------------------------------------------------------------------------
    def onLinearSpeedControlButtonReleaseEvent( self, widget, event ):
        
        if event.button == 1:
            self.controlActive = False
            self.viewXY.queue_draw()

#---------------------------------------------------------------------------
    def onAngSpeedControlButtonPressEvent( self, widget, event ):
        
        if event.button == 1:
            self.updateNormalisedZ( event.y )
            self.controlActive = True
            self.viewXY.queue_draw()

#---------------------------------------------------------------------------
    def onAngSpeedControlButtonReleaseEvent( self, widget, event ):
        
        if event.button == 1:
            self.controlActive = False
            self.viewXY.queue_draw()


#---------------------------------------------------------------------------
    def onScaleLinearSpeedMoveSlider(self, range, scrolltype)
        


#---------------------------------------------------------------------------


#---------------------------------------------------------------------------


#---------------------------------------------------------------------------


#---------------------------------------------------------------------------
    def update( self ):
    
        while 1:

	        maxDepthSpeed = self.spinMaxDepthSpeed.get_value()	    
            maxLinearSpeed = self.spinMaxLinearSpeed.get_value()
            maxAngularSpeed = self.spinMaxAngularSpeed.get_value()*math.pi/180.0

            if self.controlActive:
                newDepthSpeed = self.normalisedDepthSpeed*maxDepthSpeed
                newLinearSpeed = self.normalisedLinearSpeed*maxLinearSpeed
                newAngularSpeed = -self.normalisedAngularSpeed*maxAngularSpeed
            else:
		        newDepthSpeed = 0.0                
		        newLinearSpeed = 0.0
                newAngularSpeed = 0.0

            if newLinearSpeed != self.linearSpeed \
                or newAngularSpeed != self.angularSpeed \
		        or newDepthSpeed != self.depthSpeed:

                # Send the new speed to player
                self.playerPos3d.set_velocity( newLinearSpeed, 0.0, newDepthSpeed, # x, y, z
			                                   0.0, 0.0, newAngularSpeed, # roll, pitch, yaw
		              		                   0 )   # State
                # Store the speeds
                self.depthSpeed = newDepthSpeed
		        self.linearSpeed = newLinearSpeed
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
