#-------------------------------------------------------------------------------
# Script that attempts to go through the first gate on the SAUC-E course by using 
# controlled turning and timed forward motion.
#-------------------------------------------------------------------------------

import sys
import time
import math

from ControlScripts import ControlScript

# Add common packages directory to path
sys.path.append( "../" )
from Controllers import Arbitrator
from ImageCaptureScript import ImageCaptureScript
import Maths

#-------------------------------------------------------------------------------
class QualifyingRunScript( ControlScript ):
    
    STATE_WAITING_TO_START = "WaitingToStart"
    STATE_DIVING = "Diving"
    STATE_TURNING_TO_GATE_1 = "TurningToGate_1"
    STATE_DRIVING_THROUGH_GATE_1 = "DrivingThroughGate_1"
    STATE_SURFACING = "Surfacing"
    
    RUN_DEPTH = 110
    FORWARD_SPEED = 0.4
    START_DELAY_TIME = 0.1*60.0
    MOVE_FORWARD_TIME = 4.0*60.0  # Will probably be caught by the net
    HEADING_TO_GATE_DEGREES = 262.0
    
    USE_IMAGE_CAPTURE = True
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3d, playerCompass, 
        playerDepthSensor, playerSonar, playerFrontCamera ):
        
        ControlScript.__init__( self, config, logger, 
            playerPos3d=playerPos3d, playerCompass=playerCompass, 
            playerDepthSensor=playerDepthSensor, playerSonar=playerSonar, 
            playerFrontCamera=playerFrontCamera )
        
        self.imageCaptureScript = ImageCaptureScript( self.config, self.logger,
            self.playerPos3d, self.playerDepthSensor, self.playerSonar, self.playerFrontCamera )
        
        # Setup the arbitrator
        self.arbitrator = Arbitrator( playerPos3d, playerCompass, playerDepthSensor )
        self.arbitrator.setControlGains(
            pitchKp=self.config.pitchKp, 
            pitchKi=self.config.pitchKi, pitchiMin=self.config.pitchiMin, pitchiMax=self.config.pitchiMax, 
            pitchKd=self.config.pitchKd,
            yawKp=self.config.yawKp, 
            yawKi=self.config.yawKi, yawiMin=self.config.yawiMin, yawiMax=self.config.yawiMax, 
            yawKd=self.config.yawKd,
            depthKp=self.config.depthKp, 
            depthKi=self.config.depthKi, depthiMin=self.config.depthiMin, depthiMax=self.config.depthiMax,
            depthKd=self.config.depthKd )
        
        # Clear timers
        self.waitTimer = 0.0
        self.delayTimer = 0.0
        
        # Move into the first state
        self.linearSpeed = 0.0
        self.delayTimer = time.time()
        self.setState( self.STATE_WAITING_TO_START )    
    
    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.USE_IMAGE_CAPTURE \
            and self.state != self.STATE_WAITING_TO_START:
            self.imageCaptureScript.update()
        
        if self.state == self.STATE_WAITING_TO_START:
            
            if curTime - self.delayTimer >= self.START_DELAY_TIME:
                self.arbitrator.setDesiredDepth( self.RUN_DEPTH )
                self.linearSpeed = 0.0
                self.setState( self.STATE_DIVING )
            
        elif self.state == self.STATE_DIVING:

            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredYaw( 
                    Maths.degToRad( self.HEADING_TO_GATE_DEGREES ) )
                self.setState( self.STATE_TURNING_TO_GATE_1 )
            
        elif self.state == self.STATE_TURNING_TO_GATE_1:
            
            if self.arbitrator.atDesiredYaw():
                self.linearSpeed = self.FORWARD_SPEED
                self.driveTimer = time.time()
                self.setState( self.STATE_DRIVING_THROUGH_GATE_1 )
                        
        elif self.state == self.STATE_DRIVING_THROUGH_GATE_1:
            
            if curTime - self.driveTimer >= self.MOVE_FORWARD_TIME:
                self.linearSpeed = 0.0
                # Turn off control to the vertical thrusters to surface
                self.arbitrator.setUncontrolledMotors(
                    leftMotorUncontrolled=False, rightMotorUncontrolled=False,
                    frontMotorUncontrolled=True, backMotorUncontrolled=True )
                self.setState( self.STATE_SURFACING )
            
        elif self.state == self.STATE_SURFACING:
            # Nothig to do
            pass
        else:
            self.logger.logError( "Unrecognised state - ({0}) - surfacing".format( self.state ) )
            self.linearSpeed = 0.0
            self.setState( self.STATE_SURFACING )
        
        self.arbitrator.update( self.linearSpeed )
        
