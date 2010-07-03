#-------------------------------------------------------------------------------
# Test script to bounce the sub up and down in an attempt to stress the 
# depth sensor
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
    STATE_RISING = "Rising"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3d, playerCompass, 
        playerDepthSensor, playerSonar, playerFrontCamera ):
        
        ControlScript.__init__( self, config, logger, 
            playerPos3d=playerPos3d, playerCompass=playerCompass, 
            playerDepthSensor=playerDepthSensor, playerSonar=playerSonar, 
            playerFrontCamera=playerFrontCamera )
        
        self.UP_DEPTH = self.config.B_upDepth
        self.DOWN_DEPTH = self.config.B_downDepth
        self.START_DELAY_TIME = self.config.B_startDelayTime
        
        self.USE_IMAGE_CAPTURE = self.config.useImageCapture
        
        self.imageCaptureScript = ImageCaptureScript( self.config, self.logger,
            self.playerPos3d, self.playerDepthSensor, self.playerSonar, self.playerFrontCamera )
        
        # Setup the arbitrator
        self.arbitrator = Arbitrator( playerPos3d, playerCompass, playerDepthSensor )
        self.arbitrator.setDesiredPitch( Maths.degToRad( -4.0 ) )
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
        self.arbitrator.setEpsilons( 
            self.config.arbitratorDepthEpsilon, 
            Maths.degToRad( self.config.arbitratorYawEpsilonDegrees ) )
        
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
            
            timeDiff = curTime - self.delayTimer
            print "timeDiff is", timeDiff, "delay is", self.START_DELAY_TIME
            
            if curTime - self.delayTimer >= self.START_DELAY_TIME:
                self.logger.logMsg( "Going to " + str( self.DOWN_DEPTH ) )
                self.arbitrator.setDesiredDepth( self.DOWN_DEPTH )
                self.linearSpeed = 0.0
                self.setState( self.STATE_DIVING )
            
        elif self.state == self.STATE_DIVING:

            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredDepth( self.UP_DEPTH )
                self.linearSpeed = 0.0
                self.setState( self.STATE_RISING )
            
        elif self.state == self.STATE_RISING:

            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredDepth( self.DOWN_DEPTH )
                self.linearSpeed = 0.0
                self.setState( self.STATE_DIVING )
        
        self.arbitrator.update( self.linearSpeed )
        
