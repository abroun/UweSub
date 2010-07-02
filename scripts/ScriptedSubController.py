#! /usr/bin/python

#-------------------------------------------------------------------------------
# Control program for submarine that executes a script
#-------------------------------------------------------------------------------

import os
from optparse import OptionParser
import sys

import cv
import yaml
from playerc import *
import Profiling
import time

from SubControllerConfig import SubControllerConfig
from Logger import Logger
from ControlScripts import TimeBasedGatesScript
from ControlScripts import ImageCaptureScript
from ControlScripts import QualifyingRunScript

#-------------------------------------------------------------------------------
class ScriptedSubController:

    #---------------------------------------------------------------------------
    def __init__( self, config = SubControllerConfig() ):

        self.config = config
        self.logger = Logger( self.config )
        self.logger.addOutputToStdOut()
        
        self.connectToPlayer()
        self.setupControlScript()
        self.lastUpdateTime = time.time()
        
    #---------------------------------------------------------------------------
    def __del__( self ):
        self.shutdown()
      
    #---------------------------------------------------------------------------
    def shutdown( self ):
        if self.playerFrontCamera != None:
            self.playerFrontCamera.unsubscribe()
        if self.playerBottomCamera != None:
            self.playerBottomCamera.unsubscribe()
        if self.playerCompass != None:
            self.playerCompass.unsubscribe()
        if self.playerDepthSensor != None:
            self.playerDepthSensor.unsubscribe()
        if self.playerSonar != None:
            self.playerSonar.unsubscribe()
        if self.playerPos3d != None:
            self.playerPos3d.unsubscribe()
        if self.playerClient != None:
            self.playerClient.disconnect()
            
    #---------------------------------------------------------------------------
    def connectToPlayer( self ):
        
        try:
            # Create a client object to connect to Player
            self.playerClient = playerc_client( None, 
                self.config.playerServerAddress, self.config.playerServerPort )
            
            # Connect it
            if self.playerClient.connect() != 0:
                raise Exception( playerc_error_str() )

            # Create proxies
            self.playerPos3d = playerc_position3d( self.playerClient, 0 )
            if self.playerPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise Exception( playerc_error_str() )
                
            self.playerCompass = playerc_imu( self.playerClient, 0 )
            if self.playerCompass.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerCompass = None
            
            self.playerDepthSensor = playerc_position1d( self.playerClient, 0 )
            if self.playerDepthSensor.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerDepthSensor = None
            
            self.playerSonar = playerc_micronsonar( self.playerClient, 0 )
            if self.playerSonar.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerSonar = None
            
            self.playerFrontCamera = playerc_camera( self.playerClient, 0 )
            if self.playerFrontCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerFrontCamera = None

            self.playerBottomCamera = playerc_camera( self.playerClient, 1 )
            if self.playerBottomCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
                self.playerBottomCamera = None

            if self.playerClient.datamode( PLAYERC_DATAMODE_PULL ) != 0:
                raise Exception( playerc_error_str() )
        
            if self.playerClient.set_replace_rule( -1, -1, PLAYER_MSGTYPE_DATA, -1, 1 ) != 0:
                raise Exception( playerc_error_str() )
        except Exception as e:
            self.logger.logError( "Exception when connecting to Player - " + str( e ) )
            sys.exit( -1 )
    
        self.logger.logMsg( "Connected to Player!" )

    #---------------------------------------------------------------------------
    def setupControlScript( self ):
        
        # TODO: Come up with a good way of choosing the control script so that
        # we can choose between control scripts without the risk of typos
        
        #self.script = TimeBasedGatesScript.TimeBasedGatesScript( self.config, self.logger,
        #    self.playerPos3d, self.playerCompass, self.playerDepthSensor, self.playerSonar )
        #self.script = ImageCaptureScript.ImageCaptureScript( self.config, self.logger,
        #    self.playerPos3d, self.playerDepthSensor, self.playerSonar, self.playerFrontCamera )
        self.script = QualifyingRunScript.QualifyingRunScript( self.config, self.logger,
            self.playerPos3d, self.playerCompass, self.playerDepthSensor, 
            self.playerSonar, self.playerFrontCamera )

    #---------------------------------------------------------------------------
    def update( self ):
        
        NUM_UPDATES_PER_SECOND = 30.0
        TIME_BETWEEN_UPDATES = 1.0 / NUM_UPDATES_PER_SECOND
        
        if self.playerClient.peek( 0 ):
            self.playerClient.read()

        curTime = time.time()
        if curTime - self.lastUpdateTime >= TIME_BETWEEN_UPDATES:
            
            self.script.update()
            self.lastUpdateTime = curTime

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

    subController = ScriptedSubController( subControllerConfig )
    while 1:
        subController.update()



    
