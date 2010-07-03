#! /usr/bin/python
#-------------------------------------------------------------------------------
# Joystick application for controlling the sub
#-------------------------------------------------------------------------------

import sys
import os.path
import shutil
import math
import matplotlib.pyplot as plt
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
from Controllers import KillMotors

#-------------------------------------------------------------------------------
class MainWindow:

    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):
            
        self.config = config

        self.controlActive = False
        self.normalisedLinearSpeed = 0.0
        self.depthSpeed = 0.0
        self.linearSpeed = 0.0
        self.angularSpeed = 0.0
        
        self.degCompassPitchAngle = 0.0
        self.arrayPitchAngles = [ 0 ]
        self.startPitchGraph = False
        
        self.degCompassYawAngle = 0.0
        self.arrayYawAngles = [ 0 ]
        self.startYawGraph = False
        
        self.degCompassRollAngle = 0.0
        
        self.depthSensorDepth = 0.0
        self.arrayDepthValues = [ 0 ]
        self.arrayDepthSpeeds = [ 0 ]
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
        
        self.killing = KillMotors( self.playerPos3d )
        
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( os.path.dirname( __file__ ) + "/MonkeyDials.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.spinMaxLinearSpeed = builder.get_object( "spinMaxLinearSpeed" )
        self.linearSpeed = builder.get_object( "scaleLinearSpeed" )
        
        self.spinPitchKp = builder.get_object( "spinPitchKp" )
        self.spinPitchKi = builder.get_object( "spinPitchKi" )
        self.spinPitchiMin = builder.get_object( "spinPitchiMin" )
        self.spinPitchiMax = builder.get_object( "spinPitchiMax" )
        self.spinPitchKd = builder.get_object( "spinPitchKd" )

        self.spinYawKp = builder.get_object( "spinYawKp" )
        self.spinYawKi = builder.get_object( "spinYawKi" )
        self.spinYawiMin = builder.get_object( "spinYawiMin" )
        self.spinYawiMax = builder.get_object( "spinYawiMax" )
        self.spinYawKd = builder.get_object( "spinYawKd" )

        self.spinDepthKp = builder.get_object( "spinDepthKp" )
        self.spinDepthKi = builder.get_object( "spinDepthKi" )
        self.spinDepthiMin = builder.get_object( "spinDepthiMin" )
        self.spinDepthiMax = builder.get_object( "spinDepthiMax" )
        self.spinDepthKd = builder.get_object( "spinDepthKd" )
        
        self.spinDesiredPitchAngle = builder.get_object( "spinDesiredPitchAngle" )
        self.spinDesiredYawAngle = builder.get_object( "spinDesiredYawAngle" )
        self.spinDesiredDepth = builder.get_object( "spinDesiredDepth" )
        
        self.lblCompassPitchAngle = builder.get_object( "lblCompassPitchAngle" )
        self.lblCompassYawAngle = builder.get_object( "lblCompassYawAngle" )
        self.lblCompassRollAngle = builder.get_object( "lblCompassRollAngle" )
        self.lblDepthSensorDepth = builder.get_object( "lblDepthSensorDepth" )
        
        self.checkKill = builder.get_object( "checkKill" )
        
        self.chkControlLeftMotor = builder.get_object( "chkControlLeftMotor" )
        self.chkControlRightMotor = builder.get_object( "chkControlRightMotor" )
        self.chkControlFrontMotor = builder.get_object( "chkControlFrontMotor" )
        self.chkControlBackMotor = builder.get_object( "chkControlBackMotor" )
        
        self.spinMaxLinearSpeed.set_value( 1.0 )
        self.spinDesiredPitchAngle.set_value( -5.0 )
        self.spinDesiredYawAngle.set_value( 180.0 )
        self.spinDesiredDepth.set_value( 7456)

        self.spinPitchKp.set_value( 3.0 )
        self.spinPitchKi.set_value( 0.0 )
        self.spinPitchiMin.set_value( -1.57 )
        self.spinPitchiMax.set_value( 1.57 )
        self.spinPitchKd.set_value( 0.0 )

        self.spinYawKp.set_value( -1.4 )
        self.spinYawKi.set_value( 0.0 )
        self.spinYawiMin.set_value( -1.57 )
        self.spinYawiMax.set_value( 1.57 )
        self.spinYawKd.set_value( 0.25 )

        self.spinDepthKp.set_value( 0.3 )
        self.spinDepthKi.set_value( 0.0 )
        self.spinDepthiMin.set_value( -1.57 )
        self.spinDepthiMax.set_value( 1.57 )
        self.spinDepthKd.set_value( 0.5 )        
        
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
    def updateNormalisedY( self, y ):
        # y -> linear speed
        maxLinearSpeed = self.spinMaxLinearSpeed.get_value()
        
        if self.controlActive:
 
             # Apply the dead zone
            if y >= -self.DEAD_ZONE and y <= self.DEAD_ZONE:
                y = 0.0

        self.normalisedLinearSpeed = -y / self.RANGE

#---------------------------------------------------------------------------
    def onScaleLinearSpeedValueChanged( self, widget, data = None ):

        y = gtk.Range.get_value(widget);
        self.updateNormalisedY( y )
        self.controlActive = True
        
#---------------------------------------------------------------------------
    def onYawPosButtonClicked( self, button ):
        time = len( self.arrayYawAngles )
        plt.clf()
        #plt.figure(1)
        plt.plot( range( time ), self.arrayYawAngles )
        plt.ylabel( 'Yaw angle [deg/s]' )
        plt.xlabel( 'Time' )
        self.startYawGraph = False
        plt.show()

    def onYawPosStartButtonClicked( self, button ):
        self.startYawGraph = True
        self.arrayYawValues = []
        self.yawpTest = []
        self.yawdTest = []
        
#---------------------------------------------------------------------------
    def onPitchPosButtonClicked( self, button ):
        time = len( self.arrayPitchAngles )
        plt.clf()
        #plt.figure(2)
        plt.plot( range( time ), self.arrayPitchAngles )
        plt.ylabel( 'Pitch angle [deg/s]' )
        plt.xlabel( 'Time' )
        self.startPitchGraph = False
        plt.show()

    def onPitchPosStartButtonClicked( self, button ):
        self.startPitchGraph = True
        self.arrayPitchAngles = []
        self.pitchpTest = []
        self.pitchdTest = []
        
#---------------------------------------------------------------------------
    def onDepthPosButtonClicked( self, button ):
        time1 = len( self.arrayDepthValues )
        plt.clf()
        plt.figure(1)
        plt.plot( range( time1 ), self.arrayDepthValues )
        plt.ylabel( 'Depth [mbars]' )
        plt.xlabel( 'Time' )
        
        time2 = len( self.arrayDepthSpeeds )
        plt.clf()
        plt.figure(2)
        plt.plot( range( time2 ), self.arrayDepthSpeeds )
        plt.ylabel( 'Depth speed [deg/s]' )
        plt.xlabel( 'Time' )
        
        self.depthSpeed
        self.startDepthGraph = False
        plt.show()

    def onDepthPosStartButtonClicked( self, button ):
        self.startDepthGraph = True
        self.arrayDepthValues = []
        arrayDepthSpeeds = []
        self.depthpTest = []
        self.depthdTest = []
        
#---------------------------------------------------------------------------
    def onKillMotorsButtonClicked( self, button ):
        self.killing.update( )
        
#---------------------------------------------------------------------------    
    def update( self ):
    
        while 1:

            # Update the compass value if needed
            if self.playerCompass != None and self.playerClient.peek( 0 ):
                self.playerClient.read()
             
                # Get compass pitch and yaw angle
                radCompassPitchAngle = self.playerCompass.pose.ppitch
                radCompassYawAngle = self.playerCompass.pose.pyaw
                radCompassRollAngle = self.playerCompass.pose.proll
                # 0 < angle < 2*pi
                while radCompassPitchAngle >= 2*math.pi:
                    radCompassPitchAngle -= 2*math.pi
                while radCompassYawAngle >= 2*math.pi:
                    radCompassYawAngle -= 2*math.pi
                while radCompassRollAngle >= 2*math.pi:
                    radCompassRollAngle -= 2*math.pi
                self.degCompassPitchAngle = radCompassPitchAngle*180.0/math.pi    # from rad to degrees
                self.degCompassYawAngle = radCompassYawAngle*180.0/math.pi    # from rad to degrees
                self.degCompassRollAngle = radCompassRollAngle*180.0/math.pi    # from rad to degrees
                #print it on the GUI
                self.lblCompassPitchAngle.set_text( "{0:.3}".format( self.degCompassPitchAngle ) )
                self.lblCompassYawAngle.set_text( "{0:.3}".format( self.degCompassYawAngle ) )
                self.lblCompassRollAngle.set_text( "{0:.3}".format( self.degCompassRollAngle ) )
            
            # Update the depth sensor value if needed                
            if self.playerDepthSensor != None and self.playerClient.peek( 0 ):
                self.playerClient.read()

                # Get pressure sensor depth
                self.depthSensorDepth = self.playerDepthSensor.pos
                self.lblDepthSensorDepth.set_text( "{0:2.3f}".format( self.depthSensorDepth ) )  
            
            maxLinearSpeed = self.spinMaxLinearSpeed.get_value() 
            
            if self.controlActive:      
                newLinearSpeed = self.normalisedLinearSpeed*maxLinearSpeed
            else: 
                newLinearSpeed = 0.0
            
            pitchKp = self.spinPitchKp.get_value()
            pitchKi = self.spinPitchKi.get_value()
            pitchiMin = self.spinPitchiMin.get_value()
            pitchiMax = self.spinPitchiMax.get_value()
            pitchKd = self.spinPitchKd.get_value()

            yawKp = self.spinYawKp.get_value()
            yawKi = self.spinYawKi.get_value()
            yawiMin = self.spinYawiMin.get_value()
            yawiMax = self.spinPitchiMax.get_value()
            yawKd = self.spinYawKd.get_value()
            
            depthKp = self.spinDepthKp.get_value()
            depthKi = self.spinDepthKi.get_value()
            depthiMin = self.spinDepthiMin.get_value()
            depthiMax = self.spinDepthiMax.get_value()
            depthKd = self.spinDepthKd.get_value()
                        
            newDesiredPitchAngle = self.spinDesiredPitchAngle.get_value()*math.pi/180.0    # from degrees to rad
            newDesiredYawAngle = self.spinDesiredYawAngle.get_value()*math.pi/180.0    # from degrees to rad
            newDesiredDepth = self.spinDesiredDepth.get_value()
            
            if self.startPitchGraph:
                self.arrayPitchAngles.append( self.degCompassPitchAngle)
                self.pitchpTest.append (self.pitchController.pitchpTerm)
                self.pitchdTest.append(self.pitchController.pitchdTerm)
                #if radCompassPitchAngle - newDesiredPitchAngle < 0.01 \
                #    and radCompassPitchAngle - newDesiredPitchAngle> -0.01:
                #    self.pitchController.iState = 0.0
                #    self.startPitchGraph = False

            if self.startYawGraph:
                mydegCompassYawAngle = self.degCompassYawAngle
                while mydegCompassYawAngle >= math.pi:
                    mydegCompassYawAngle -= 2*math.pi
                while mydegCompassYawAngle < -math.pi:
                    mydegCompassYawAngle += 2*math.pi
                
                self.arrayYawAngles.append( mydegCompassYawAngle )
                self.yawpTest.append (self.yawController.yawpTerm)
                self.yawdTest.append(self.yawController.yawdTerm)
              #  if radCompassYawAngle - newDesiredYawAngle < 0.01 \
               #     and radCompassYawAngle - newDesiredYawAngle> -0.01:
                #    self.yawController.iState = 0.0
                    
                    #figure(2)
                    #plot(range(len(self.yawpTest)),self.pTest,'r',\
                         #range(len(self.yawiTest)),self.iTest,'k',\
                         #range(len(self.yawdTest)),self.dTest,'m')
                    #xlabel('Time')
                    #ylabel('yaw pTerm, yaw iTerm & yaw dTerm')
                    #show()
                #    self.startYawGraph = False
                    
            if self.startDepthGraph:
                self.arrayDepthValues.append( self.depthSensorDepth)
                self.arrayDepthSpeeds.append( self.depthController.depthSpeed)
                self.depthpTest.append (self.depthController.depthpTerm)
                self.depthdTest.append(self.depthController.depthdTerm)
               #if self.depthSensorDepth - newDesiredDepth < 0.01 \
                #    and self.depthSensorDepth - newDesiredDepth> -0.01:
                 #   self.depthController.iState = 0.0
                  #  self.startDepthGraph = False
               
            if self.checkKill.get_active():
                self.killing.update( )
            else:
                self.arbitrator.setControlGains( pitchKp, pitchKi, pitchiMin, pitchiMax, pitchKd,
                                                   yawKp,   yawKi,   yawiMin,   yawiMax,    yawKd,
                                                 depthKp, depthKi, depthiMin, depthiMax, depthKd )
                self.arbitrator.setDesiredState( newDesiredPitchAngle, newDesiredYawAngle, newDesiredDepth )   # rad
                self.arbitrator.setUncontrolledMotors(
                    self.chkControlLeftMotor.get_active(), self.chkControlRightMotor.get_active(),
                    self.chkControlFrontMotor.get_active(), self.chkControlBackMotor.get_active() )
                self.arbitrator.update( newLinearSpeed )         
            
            if newLinearSpeed != self.linearSpeed:
                # Store the speed
                self.linearSpeed = newLinearSpeed
                
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
        subControllerConfig.addUnsetVariables()
        configFile.close()

    mainWindow = MainWindow( subControllerConfig )
    mainWindow.main()
