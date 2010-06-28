#-------------------------------------------------------------------------------
# Script that attempts to complete the first part of the SAUC-E course by using 
# controlled turning and timed forward motion.
#-------------------------------------------------------------------------------

import sys
import time
import math

from ControlScripts import ControlScript

# Add common packages directory to path
sys.path.append( "../" )
from Controllers import Arbitrator
import Maths

#-------------------------------------------------------------------------------
class TimeBasedGatesScript( ControlScript ):
    
    STATE_DIVING = "Diving"
    STATE_TURNING_TO_GATE_1 = "TurningToGate_1"
    STATE_DRIVING_THROUGH_GATE_1 = "DrivingThroughGate_1"
    STATE_TURNING_TO_GATE_2 = "TurningToGate_2"
    STATE_DRIVING_THROUGH_GATE_2 = "DrivingThroughGate_2"
    STATE_TURNING_TO_START = "TurningToStart"
    STATE_DRIVING_BACK_TO_START = "DrivingBackToStart"
    STATE_SURFACING = "Surfacing"
    STATE_FINISHED = "Finished"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3D, playerCompass, 
        playerDepthSensor, playerSonar = None ):
        
        ControlScript.__init__( self, config, logger, playerPos3D, playerCompass, 
            playerDepthSensor, playerSonar )
        
        self.arbitrator = Arbitrator( playerPos3D, playerCompass, playerDepthSensor )
        self.arbitrator.setDesiredDepth( -1.0 )
        self.linearSpeed = 0.0
        self.setState( self.STATE_DIVING )
        self.driveTimer = time.time()
    
    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.state == self.STATE_DIVING:

            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredYaw( Maths.degToRad( 0.0 ) )
                self.setState( self.STATE_TURNING_TO_GATE_1 )
            
        elif self.state == self.STATE_TURNING_TO_GATE_1:
            
            if self.arbitrator.atDesiredYaw():
                self.linearSpeed = 1.0
                self.driveTimer = time.time()
                self.setState( self.STATE_DRIVING_THROUGH_GATE_1 )
                        
        elif self.state == self.STATE_DRIVING_THROUGH_GATE_1:
            
            if curTime - self.driveTimer >= 20.0:
                self.linearSpeed = 0.0
                self.arbitrator.setDesiredYaw( Maths.degToRad( 180.0 ) )
                self.setState( self.STATE_TURNING_TO_GATE_2 )
            
        elif self.state == self.STATE_TURNING_TO_GATE_2:
            
            if self.arbitrator.atDesiredYaw():
                self.linearSpeed = 1.0
                self.driveTimer = time.time()
                self.setState( self.STATE_DRIVING_THROUGH_GATE_2 )
            
        elif self.state == self.STATE_DRIVING_THROUGH_GATE_2:
            
            if curTime - self.driveTimer >= 40.0:
                self.linearSpeed = 0.0
                self.arbitrator.setDesiredYaw( Maths.degToRad( 0.0 ) )
                self.setState( self.STATE_TURNING_TO_START )
            
        elif self.state == self.STATE_TURNING_TO_START:
            
            if self.arbitrator.atDesiredYaw():
                self.linearSpeed = 1.0
                self.driveTimer = time.time()
                self.setState( self.STATE_DRIVING_BACK_TO_START )
            
        elif self.state == self.STATE_DRIVING_BACK_TO_START:
            
            if curTime - self.driveTimer >= 20.0:
                self.linearSpeed = 0.0
                self.arbitrator.setDesiredDepth( 0.0 )
                self.setState( self.STATE_SURFACING )
            
        elif self.state == self.STATE_SURFACING:
            
            if self.arbitrator.atDesiredDepth():
                self.setState( self.STATE_FINISHED )
            
        elif self.state == self.STATE_FINISHED:
            # Nothig to do
            pass
        else:
            self.logger.logError( "Unrecognised state - surfacing" )
            self.setState( self.STATE_SURFACING )
        
        self.arbitrator.update( self.linearSpeed )
        
