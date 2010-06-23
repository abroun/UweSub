#! /usr/bin/python
#-------------------------------------------------------------------------------
# Joystick application for controlling the sub
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
from Controllers import PitchControl
from Controllers import YawControl
from Controllers import DepthControl
from Controllers import Arbitrator

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
        
        self.degCompassPitchAngle = 0.0
        self.arrayPitchAngles = [ 0 ]
        self.startPitchGraph = False
        
        self.degCompassYawAngle = 0.0
        self.arrayYawAngles = [ 0 ]
        self.startYawGraph = False
        
        self.depthSensorDepth = 0.0
        self.arrayDepthValues = [ 0 ]
        self.startDepthGraph = False

        self.pitchpTest = []
        self.pitchiTest = []
        self.pitchdTest = []
                
        self.yawpTest = []
        self.yawiTest = []
        self.yawdTest = []

        self.depthpTest = []
        self.depthiTest = []
        self.depthdTest = []
        
        self.connectToPlayer()
        
        self.pitchController = PitchControl( self.playerPos3d,
            self.playerCompass, self.playerSimPos3d )
        self.yawController = YawControl( self.playerPos3d,
            self.playerCompass, self.playerSimPos3d )
        self.depthController = DepthControl( self.playerPos3d,
            self.playerDepthSensor, self.playerSimPos3d )
        
        self.arbitrator = Arbitrator( self.playerPos3d,
            self.playerCompass, self.playerDepthSensor, self.playerSimPos3d )
        
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) + "/MonkeyDials.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.spinMaxDepthSpeed = builder.get_object( "spinMaxDepthSpeed" )
        self.spinMaxLinearSpeed = builder.get_object( "spinMaxLinearSpeed" )
        self.spinMaxAngularSpeed = builder.get_object( "spinMaxAngularSpeed" )
        self.linearSpeed = builder.get_object( "scaleLinearSpeed" )
        self.angularSpeed = builder.get_object( "scaleAngularSpeed" )
        self.depthSpeed = builder.get_object( "scaleDepthSpeed" )
        self.spinDesiredPitchAngle = builder.get_object( "spinDesiredPitchAngle" )
        self.spinDesiredYawAngle = builder.get_object( "spinDesiredYawAngle" )
        self.spinDesiredDepth = builder.get_object( "spinDesiredDepth" )
        
        self.lblCompassPitchAngle = builder.get_object( "lblCompassPitchAngle" )
        self.lblCompassYawAngle = builder.get_object( "lblCompassYawAngle" )
        self.lblDepthSensorDepth = builder.get_object( "lblDepthSensorDepth" )
        
        self.spinMaxLinearSpeed.set_value( 2.0 )
        self.spinMaxAngularSpeed.set_value( 30.0 )
        self.spinMaxDepthSpeed.set_value( 2.0 )
        
        self.spinDesiredPitchAngle.set_value( 0.0 )
        self.spinDesiredYawAngle.set_value( 0.0 )
        self.spinDesiredDepth.set_value( 1.0 )
        
        
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
            
            self.playerDepthSensor = playerc_position1d( self.playerClient, 0 )
            if self.playerDepthSensor.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerDepthSensor = None

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
        plot( range( time ), self.arrayYawAngles )
        ylabel( 'Yaw angle [deg/s]' )
        xlabel( 'Time' )
        show()

#---------------------------------------------------------------------------
    def onPitchPosButtonClicked( self, button ):
        time = len( self.arrayPitchAngles )
        figure(2)
        plot( range( time ), self.arrayPitchAngles )
        ylabel( 'Pitch angle [deg/s]' )
        xlabel( 'Time' )
        show()

#---------------------------------------------------------------------------
    def onDepthPosButtonClicked( self, button ):
        time = len( self.arrayDepthValues )
        figure(3)
        plot( range( time ), self.arrayDepthValues )
        ylabel( 'Pitch angle [deg/s]' )
        xlabel( 'Time' )
        show()

#---------------------------------------------------------------------------    
    def update( self ):
    
        while 1:

            # Update the compass value if needed
            if self.playerCompass != None and self.playerClient.peek( 0 ):
                self.playerClient.read()
             
                # Get compass pitch and yaw angle
                radCompassPitchAngle = self.playerCompass.pose.ppitch
                radCompassYawAngle = self.playerCompass.pose.pyaw
                # 0 < angle < 2*pi
                while radCompassPitchAngle >= 2*math.pi:
                    radCompassPitchAngle -= 2*math.pi
                while radCompassYawAngle >= 2*math.pi:
                    radCompassYawAngle -= 2*math.pi
                self.degCompassPitchAngle = radCompassPitchAngle*180.0/math.pi    # from rad to degrees
                self.degCompassYawAngle = radCompassYawAngle*180.0/math.pi    # from rad to degrees
                #print it on the GUI
                self.lblCompassPitchAngle.set_text( "{0:.3}".format( self.degCompassPitchAngle ) )
                self.lblCompassYawAngle.set_text( "{0:.3}".format( self.degCompassYawAngle ) )
            
            # Update the depth sensor value if needed                
            if self.playerDepthSensor != None and self.playerClient.peek( 0 ):
                self.playerClient.read()

                # Get pressure sensor depth
                self.depthSensorDepth = self.playerDepthSensor.pos
                self.lblDepthSensorDepth.set_text( "{0:.3}".format( self.depthSensorDepth ) )  
            
            maxLinearSpeed = self.spinMaxLinearSpeed.get_value() 
            maxAngularSpeed = self.spinMaxAngularSpeed.get_value()*math.pi/180.0    # from degrees to rad
            maxDepthSpeed = self.spinMaxDepthSpeed.get_value()      
            
            if self.controlActive:
                newDepthSpeed = -self.normalisedDepthSpeed*maxDepthSpeed
                if newDepthSpeed == 0.0:
                    newDepthSpeed = 0.05     # positive boyancy - it can also fly after a while           
                newLinearSpeed = self.normalisedLinearSpeed*maxLinearSpeed
                newAngularSpeed = self.normalisedAngularSpeed*maxAngularSpeed
            else:
                newDepthSpeed = 0.0  
                newLinearSpeed = 0.0
                newAngularSpeed = 0.0
            
            newDesiredPitchAngle = self.spinDesiredPitchAngle.get_value()*math.pi/180.0    # from degrees to rad
            newDesiredYawAngle = self.spinDesiredYawAngle.get_value()*math.pi/180.0    # from degrees to rad
            newDesiredDepth = self.spinDesiredDepth.get_value()
            
            if self.degCompassPitchAngle > 0.05:
                self.startPitchGraph = True
            if self.startPitchGraph:
                self.arrayPitchAngles.append( self.degCompassPitchAngle)
                self.pitchpTest.append (self.pitchController.pitchpTerm)
                self.pitchdTest.append(self.pitchController.pitchdTerm)
                if radCompassPitchAngle - newDesiredPitchAngle < 0.01 \
                    and radCompassPitchAngle - newDesiredPitchAngle> -0.01:
                    self.pitchController.iState = 0.0
                    self.startPitchGraph = False

            if self.degCompassYawAngle > 0.05:
                self.startYawGraph = True
            if self.startYawGraph:
                self.arrayYawAngles.append( self.degCompassYawAngle)
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
                    self.startYawGraph = False
                    
            if self.depthSensorDepth > 0.005:
                self.startDepthGraph = True
            if self.startDepthGraph:
                self.arrayDepthValues.append( self.depthSensorDepth)
                self.depthpTest.append (self.depthController.depthpTerm)
                self.depthdTest.append(self.depthController.depthdTerm)
                if self.depthSensorDepth - newDesiredDepth < 0.01 \
                    and self.depthSensorDepth - newDesiredDepth> -0.01:
                    self.depthController.iState = 0.0
                    self.startDepthGraph = False
                            
            self.arbitrator.setDesiredState( newDesiredPitchAngle, newDesiredYawAngle, newDesiredDepth )   # rad
            self.arbitrator.update( newLinearSpeed )         
            
            if newLinearSpeed != self.linearSpeed \
                or newAngularSpeed != self.angularSpeed \
		        or newDepthSpeed != self.depthSpeed:

                # Store the speeds
                self.linearSpeed = newLinearSpeed
                self.angularSpeed = newAngularSpeed
                self.depthSpeed = newDepthSpeed
                
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
