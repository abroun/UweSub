#! /usr/bin/python
#-------------------------------------------------------------------------------
# Simple joystick application for controlling the sub
#-------------------------------------------------------------------------------

import sys
import os.path
import shutil
import math
from pylab import *
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
from Controllers import YawControl

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
        
        self.arrayYawAngles = [ 0 ]
        self.startGraph = False
        
        self.yawpTest = []
        self.yawiTest = []
        self.yawdTest = []

        self.connectToPlayer()
        self.yawController = YawControl( self.playerPos3d,
            self.playerCompass, self.playerSimPos3d )
       
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) + "/MonkeyDials.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.spinMaxDepthSpeed = builder.get_object( "spinMaxDepthSpeed" )
        self.spinMaxLinearSpeed = builder.get_object( "spinMaxLinearSpeed" )
        self.spinMaxAngularSpeed = builder.get_object( "spinMaxAngularSpeed" )
        self.spinDesiredYawAngle = builder.get_object( "spinDesiredYawAngle" )
        self.depthSpeed = builder.get_object( "scaleDepthSpeed" )
        self.linearSpeed = builder.get_object( "scaleLinearSpeed" )
        self.angularSpeed = builder.get_object( "scaleAngularSpeed" )
        self.lblCompassYawAngle = builder.get_object( "lblCompassAngle" )

        self.spinMaxDepthSpeed.set_value( 2.0 )
        self.spinMaxLinearSpeed.set_value( 2.0 )
        self.spinMaxAngularSpeed.set_value( 30.0 )

    	self.RANGE = 100
        self.DEAD_ZONE = self.RANGE*0.01

        builder.connect_signals( self )
        
        self.window.show()
        
        #self.yawController.foo = 10
        #print dir( self.yawController )

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
            self.playerSimPos3d = playerc_position3d( self.playerClient, 1 )
            if self.playerSimPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerSimPos3d = None
                
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
        
        maxDepthSpeed = self.spinMaxDepthSpeed.get_value()

        if self.controlActive:
            
            # Apply the dead zone
            if z >= -self.DEAD_ZONE and z <= self.DEAD_ZONE:
                z = 0.0

        self.normalisedDepthSpeed = z / self.RANGE
   
#---------------------------------------------------------------------------
    def updateNormalisedY( self, y ):
        # y -> linear speed
        maxLinearSpeed = self.spinMaxLinearSpeed.get_value()
        
        if self.controlActive:
 
             # Apply the dead zone
            if y >= -self.DEAD_ZONE and y <= self.DEAD_ZONE:
                y = 0.0

        self.normalisedLinearSpeed = y / self.RANGE
        
#---------------------------------------------------------------------------
    def updateNormalisedX( self, x ):
	# x -> angular speed
        maxAngularSpeed = self.spinMaxAngularSpeed.get_value()*math.pi/180.0    # from degrees to rad

        if self.controlActive:

            # Apply the dead zone
            if x >= -self.DEAD_ZONE and x <= self.DEAD_ZONE:
                x = 0.0

        self.normalisedAngularSpeed = x / self.RANGE

#---------------------------------------------------------------------------
    def onScaleDepthSpeedValueChanged( self, widget, data = None ):
        z = gtk.Range.get_value(widget);
        self.updateNormalisedZ( z )
        self.controlActive = True

#---------------------------------------------------------------------------
    def onScaleLinearSpeedValueChanged( self, widget, data = None ):

        y = gtk.Range.get_value(widget);
        self.updateNormalisedY( y )
        self.controlActive = True
        
#---------------------------------------------------------------------------
    def onScaleAngularSpeedValueChanged( self, widget, data = None ):

        x = gtk.Range.get_value(widget);
        self.updateNormalisedX( x )
        self.controlActive = True
        
#---------------------------------------------------------------------------
    def onYawPosButtonClicked( self, button ):
        time = len( self.arrayYawAngles )
        figure(1)
        plot(range( time ), self.arrayYawAngles)
        ylabel('Yaw angle [deg/s]')
        xlabel('Time')
        #hold()
        show()

#---------------------------------------------------------------------------
    def onPitchPosButtonClicked( self, button ):
        #time = len( self.arrayYawAngles )
        #plot(range( time ), self.arrayPitchAngles)
        ylabel('Pitch angle [deg/s]')
        xlabel('Time')
        show()

#---------------------------------------------------------------------------
    def onDepthPosButtonClicked( self, button ):
        pass

#---------------------------------------------------------------------------    
    def update( self ):
    
        while 1:

            # Update the compass value if needed
            if self.playerCompass != None and self.playerClient.peek( 0 ):
                self.playerClient.read()
             
                # Get compass angle
                radCompassYawAngle = self.playerCompass.pose.pyaw
                # 0 < angle < 2*pi
                while radCompassYawAngle >= 2*math.pi:
                    radCompassYawAngle -= 2*math.pi

                degCompassYawAngle = radCompassYawAngle*180.0/math.pi    # from rad to degrees
                self.lblCompassYawAngle.set_text( "{0:.3}".format( degCompassYawAngle ) )    #print it on the GUI
               
            maxDepthSpeed = self.spinMaxDepthSpeed.get_value()	    
            maxLinearSpeed = self.spinMaxLinearSpeed.get_value() 
            
            maxAngularSpeed = self.spinMaxAngularSpeed.get_value()*math.pi/180.0    # from degrees to rad

            if self.controlActive:
                newDepthSpeed = -self.normalisedDepthSpeed*maxDepthSpeed
                if newDepthSpeed == 0.0:
                    newDepthSpeed = 0.05     # positive boyancy - it can also fly after a while ^o^            
                newLinearSpeed = self.normalisedLinearSpeed*maxLinearSpeed
                newAngularSpeed = self.normalisedAngularSpeed*maxAngularSpeed
            else:
                newDepthSpeed = 0.0  
                newLinearSpeed = 0.0
                newAngularSpeed = 0.0
            
            newDesiredYawAngle = self.spinDesiredYawAngle.get_value()*math.pi/180.0    # from degrees to rad       
            
            if degCompassYawAngle > 0.05:
                self.startGraph = True
            if self.startGraph:
                self.arrayYawAngles.append( degCompassYawAngle)
                self.yawpTest.append (self.yawController.yawpTerm)
                self.yawdTest.append(self.yawController.yawdTerm)
                if radCompassYawAngle - newDesiredYawAngle < 0.01 \
                    and radCompassYawAngle - newDesiredYawAngle> -0.01:
                    self.yawController.iState = 0.0
                    
                    #figure(2)
                    #plot(range(len(self.yawpTest)),self.pTest,'r',\
                         #range(len(self.yawiTest)),self.iTest,'k',\
                         #range(len(self.yawdTest)),self.dTest,'m')
                    #xlabel('Time')
                    #ylabel('yaw pTerm, yaw iTerm & yaw dTerm')
                    #show()
                    self.startGraph = False
                
            self.yawController.setDesiredState( newDesiredPitchAngle, newDesiredYawAngle, newDepth )   # rad
            self.yawController.update( newLinearSpeed )         
            
            
            if newLinearSpeed != self.linearSpeed \
                or newAngularSpeed != self.angularSpeed \
		        or newDepthSpeed != self.depthSpeed:

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
