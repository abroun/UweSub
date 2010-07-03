#-------------------------------------------------------------------------------
# Script tracking the boy and cutting the rope
#-------------------------------------------------------------------------------


import sys
import time
import math

from ControlScripts import ControlScript

# Add common packages directory to path
sys.path.append( "../" )
from Controllers import Arbitrator
from ColourTracker import bouy_finder
import Maths


class OrangeBallScript ( ControlScript ):    
    
     #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3D, playerCompass, 
        playerDepthSensor, playerSonar = None ):
        
        self.arbitrator = Arbitrator( playerPos3D, playerCompass, playerDepthSensor )
        self.ballFinder = bouy_finder()

        self.pitchAngle = -5.0                       # temporary value - zero pitch
        self.initYawAngle = Maths.degToRad( 85.0 )   # temporary value - heading towards the wall
        self.initDepth = 7450.0                      # temporary value - 0.5 metres beneath the surface
        self.cuttingDepth = 7470.0
        self.noLinearSpeed = 0.0
        self.movingLinearSpeed = 1.0
        self.arbitrator.setDesiredState( pitchAngle, initYawAngle, initDepth )
        self.arbitrator.update( self.noLinearSpeed )
        self.oneMetresArea = 2700                    # rough estimate        
        
        self.forwardTimer = time.time()
        self.closeEnoughFlag = 0.0
        self.detectOrangeFlag = 0.0
        self.ballArea = 0.0
        self.lastBallArea = 0.0
        

    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.closeEnoughFlag == 0.0:
            if self.arbitrator.atDesiredYaw() and self.arbitrator.atDesiredDepth():
                self.arbitrator.update( self.movingLinearSpeed )
                self.forwardTimer = time.time()
            
            if curTime - self.forwardTimer >= 30.0:         # temporary value - determined by test
                self.arbitrator.update( self.noLinearSpeed )
                self.closeEnoughFlag == 1.0

        else:
            angle = self.initYawAngle
            lefScanAngleRange = self.initYawAngle - math.pi/2
            rightScanAngleRange = self.initYawAngle + math.pi/2
            
            while angle >= lefScanAngleRange and self.detectOrangeFlag == 0.0:
                self.arbitrator.setDesiredYawAngle( angle )
                self.arbitrator.update( self.noLinearSpeed )
                self.ballFinder.run( )
                self.detectOrangeFlag = self.ballFinder.target_aquired
                if self.detectOrangeFlag == 0.0:
                    angle -= Maths.degToRad( 10 )
                            
            while angle <= rightScanAngleRange and self.detectOrangeFlag == 0:
                self.arbitrator.setDesiredYawAngle( angle )
                self.arbitrator.update( noLinearSpeed )
                self.ballFinder.run( )
                self.detectOrangeFlag = self.ballFinder.target_aquired
                if self.detectOrangeFlag == 0.0:
                    angle += Maths.degToRad( 10 )
            
            if self.detectOrangeFlag == 1.0:
                compassYawAngle = self.playerCompass.pose.pyaw
                self.ballFinder.run( )
                ballX = self.ballFinder.corr_x
                self.ballArea = self.ballFinder.pixel_count
                #if self.ballArea > twoMetresArea and self.ballArea < onefiveMetresArea:
                    #distance = 2.0
                #elif self.ballArea > onefiveMetresArea and self.ballArea < oneMetresArea:
                    #distance = 1.5
                #elif self.ballArea > onefiveMetresArea and self.ballArea < oneMetresArea:
                    #distance = 1.0
                while ballX > 10 or ballX < -10:
                    if ballX > 0:
                        newYaw = compassYawAngle + Maths.degToRad( 5 )
                    elif ballX < 0:
                        newYaw = compassYawAngle - Maths.degToRad( 5 )
                    self.arbitrator.setDesiredYaw( newYaw )
                    self.arbitrator.update ( movingLinearSpeed )    # don't wait for the yaw control, because it's a rough estimate anyway
                    if self.ballArea > self.oneMetresArea:               # needs to be set
                        self.arbitrator.setDesiredDepth( self.cuttingDepth )
                        self.arbitrator.update( noLinearSpeed )
                        if atDesiredDepth():
                            self.arbitrator.update( movingLinearSpeed )
                            #"activate cutter"
                            