#-------------------------------------------------------------------------------
# Script tracking the boy and cutting the rope
#-------------------------------------------------------------------------------

import sys
import time
import math

from ControlScripts import ControlScript
from Controllers import Arbitrator
from JamesStuff import James

# Add common packages directory to path
sys.path.append( "../" )

import Maths


class OrangeBallScript:
    
    
    
     #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3D, playerCompass, 
        playerDepthSensor, playerSonar = None ):
        
        ControlScript.__init__( self, config, logger, playerPos3D, playerCompass, 
            playerDepthSensor, playerSonar )
        
        self.arbitrator = Arbitrator( playerPos3D, playerCompass, playerDepthSensor )
        self.jamesFinder = James1 ()
        self.jamesAnalyser = James2 ()
        
        self.targetPitchAngle = 0.0                      # temporary value - zero pitch, might be Maths.degToRad( -5 )
        self.targetYawAngle = Maths.degToRad( 85.0 )     # temporary value - heading towards the wall
        self.targetDepth = 7460.0                        # temporary value - 0.5 metres beneath the surface
        self.linearSpeed = 0.0
        self.arbitrator.setDesiredState( targetPitchAngle, targetYawAngle, targetDepth )
        self.arbitrator.update( self.linearSpeed )
        
        self.forwardTimer = time.time()
        self.closeEnoughFlag = 0.0
        self.detectOrangeFlag = 0.0
        self.ballArea = 0.0
        self.relativeBallAngle = 0.0

    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.closeEnoughFlag == 0.0:
            if self.arbitrator.atDesiredYaw() and self.arbitrator.atDesiredDepth():
                self.linearSpeed = 1.0                   # temporary value - determined by test
                self.arbitrator.update( self.linearSpeed )
                self.forwardTimer = time.time()
            
            if curTime - self.forwardTimer >= 30.0:         # temporary value - determined by test
                self.linearSpeed = 0.0
                self.arbitrator.update( self.linearSpeed )
                self.closeEnoughFlag == 1.0
        
        else:
            angle = targetYawAngle
            lefScanAngleRange = targetYawAngle - math.pi/2
            rightScanAngleRange = targetYawAngle + math.pi/2
            
            while angle >= lefScanAngleRange and self.detectOrangeFlag == 0:
                self.arbitrator.setDesiredYawAngle( angle )
                self.detectOrangeFlag = self.jamesFinder.something
                angle -= Maths.degToRad( 10 )
                            
            while angle <= rightScanAngleRange and self.detectOrangeFlag == 0:
                self.arbitrator.setDesiredYawAngle( angle )
                self.detectOrangeFlag = self.jamesFinder.something
                angle += Maths.degToRad( 10 )
            
            if self.detectOrangeFlag == 1.0:
                self.relativeBallAngle = self.james.angle
                self.ballArea = self.james.area
            
            
            
            
            
            
            self.objectTargetSize = # some value
            self.objectTargetAngle = # some value
            self.cuttingDepth = # some value
            
            
            if self.relativeBallArea == self.objectTargetSize and self.relativeBallAngle == self.objectTargetAngle
                decrease depth 
                move forward
                activate cutter
                
            elif self.relativeBallArea == self.objectTargetSize
                self.arbitrator.setUncontrolledMotors(1,1,0,0) #stop forward motion
            
            elif self.arbitrator.atDesiredDepth():    
                compassYawAngle = self.playerCompass.pose.pyaw      # rad
                ballAngle = compassYawAngle + relativeBallAngle 
                self.arbitrator.setDesiredYaw( ballAngle )
                    
            else
                self.arbitrator.setDesiredDepth( self.targetDepth ) # make sure the sub is at the correct depth