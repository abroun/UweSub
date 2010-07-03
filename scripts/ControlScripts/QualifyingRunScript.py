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
    
    STATE_DIVING = "Diving"
    STATE_TURNING_TO_GATE_1 = "TurningToGate_1"
    STATE_DRIVING_THROUGH_GATE_1 = "DrivingThroughGate_1"
    STATE_DRIVING_BACK_TO_START = "DrivingBackToStart"
    STATE_SURFACING = "Surfacing"
    STATE_FINISHED = "Finished"
    
    RUN_DEPTH = 400
    FORWARD_SPEED = 0.4
    BACKWARD_SPEED = -0.5
    MOVE_FORWARD_TIME = 20.0
    MOVE_BACKWARD_TIME = 20.0
    
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
            pitchKp=3.0, pitchKi=0.0, pitchiMin=-1.57, pitchiMax=1.57, pitchKd=0.0,
            yawKp=-1.4, yawKi=0.0, yawiMin=-1.57, yawiMax=-1.57, yawKd=0.25,
            depthKp=0.3, depthKi=0.0, depthiMin=-1.57, depthiMax=1.57, depthKd=0.0 ):
        
        # Move into the first state
        self.arbitrator.setDesiredDepth( self.RUN_DEPTH )
        self.linearSpeed = 0.0
        self.setState( self.STATE_DIVING )
        self.driveTimer = time.time()
    
    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.USE_IMAGE_CAPTURE:
            self.imageCaptureScript.update()
        
        if self.state == self.STATE_DIVING:

            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredYaw( Maths.degToRad( 79.0 ) )
                self.setState( self.STATE_TURNING_TO_GATE_1 )
            
        elif self.state == self.STATE_TURNING_TO_GATE_1:
            
            if self.arbitrator.atDesiredYaw():
                self.linearSpeed = self.FORWARD_SPEED
                self.driveTimer = time.time()
                self.setState( self.STATE_DRIVING_THROUGH_GATE_1 )
                        
        elif self.state == self.STATE_DRIVING_THROUGH_GATE_1:
            
            if curTime - self.driveTimer >= self.MOVE_FORWARD_TIME:
                self.linearSpeed = self.BACKWARD_SPEED
                self.driveTimer = time.time()
                self.setState( self.STATE_DRIVING_BACK_TO_START )
            
        elif self.state == self.STATE_DRIVING_BACK_TO_START:
            
            if curTime - self.driveTimer >= MOVE_BACKWARD_TIME:
                self.linearSpeed = 0.0
                # Turn off control to the vertical thrusters to surface
                self.arbitrator.setUncontrolledMotors(
                    leftMotorUncontrolled=False, rightMotorUncontrolled=False,
                    frontMotorUncontrolled=True, backMotorUncontrolled=True )
                self.setState( self.STATE_SURFACING )
            
        elif self.state == self.STATE_SURFACING:
            # Nothing to do
            pass
        else:
            self.logger.logError( "Unrecognised state - surfacing" )
            self.linearSpeed = 0.0
            self.setState( self.STATE_SURFACING )
        
        self.arbitrator.update( self.linearSpeed )
