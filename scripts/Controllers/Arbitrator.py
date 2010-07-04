#-------------------------------------------------------------------------------
# An arbitration mechanism for the control schemes
#-------------------------------------------------------------------------------

import math
import time
import sys

from Controllers import PitchControl
from Controllers import YawControl
from Controllers import DepthControl

# Add common packages directory to path
sys.path.append( "../" )
import Maths

#-------------------------------------------------------------------------------
class Arbitrator:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerDepthSensor, playerSimPos3D = None, logger = None ):
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerDepthSensor = playerDepthSensor
        self.playerSimPos3D = playerSimPos3D
        self.logger = logger
        
        self.pitchController = PitchControl( self.playerPos3D,
            self.playerCompass, self.playerSimPos3D )
        self.yawController = YawControl( self.playerPos3D,
            self.playerCompass, self.playerSimPos3D )
        self.depthController = DepthControl( self.playerPos3D,
            self.playerDepthSensor, self.playerSimPos3D )
        self.leftMotorUncontrolled = False
        self.rightMotorUncontrolled = False
        self.frontMotorUncontrolled = False
        self.backMotorUncontrolled = False
        
        self.depthEpsilon = 10
        self.yawEpsilon = Maths.degToRad( 2.5 )
        
        self.lastTime = time.time()
        self.lastDepth = -1.0
        self.depthControlDisabled = False
        self.numIdenticalDepthReadings = 0

    #---------------------------------------------------------------------------
    def setControlGains( self,  pitchKp, pitchKi, pitchiMin, pitchiMax, pitchKd,
                                  yawKp,   yawKi,   yawiMin,   yawiMax,    yawKd,
                                depthKp, depthKi, depthiMin, depthiMax, depthKd ):
        self.pitchController.setPitchGains( pitchKp, pitchKi, pitchiMin, pitchiMax, pitchKd )
        self.yawController.setYawGains( yawKp, yawKi, yawiMin, yawiMax, yawKd  )
        self.depthController.setDepthGains( depthKp, depthKi, depthiMin, depthiMax, depthKd  )

    #---------------------------------------------------------------------------
    def setEpsilons( self, depthEpsilon, yawEpsilon ):
        self.depthEpsilon = depthEpsilon
        self.yawEpsilon = yawEpsilon

    #---------------------------------------------------------------------------
    def setDesiredState( self, pitchAngle, yawAngle, depth ):        
        self.pitchController.setDesiredPitchAngle( pitchAngle )     # rad
        self.yawController.setDesiredYawAngle( yawAngle )           # rad
        self.depthController.setDesiredDepth( depth )               # m
        
    #---------------------------------------------------------------------------
    def setDesiredYaw( self, yawAngle ):
        self.yawController.setDesiredYawAngle( yawAngle )

    #---------------------------------------------------------------------------
    def setDesiredDepth( self, depth ):
        self.depthController.setDesiredDepth( depth )
   
    #---------------------------------------------------------------------------
    def setDesiredPitch( self, pitch ):
        self.pitchController.setDesiredPitchAngle( pitch )
   
    #---------------------------------------------------------------------------
    def setUncontrolledMotors( self, 
        leftMotorUncontrolled, rightMotorUncontrolled,
        frontMotorUncontrolled, backMotorUncontrolled ):
        
        self.leftMotorUncontrolled = leftMotorUncontrolled
        self.rightMotorUncontrolled = rightMotorUncontrolled
        self.frontMotorUncontrolled = frontMotorUncontrolled
        self.backMotorUncontrolled = backMotorUncontrolled
        
    #---------------------------------------------------------------------------
    def atDesiredYaw( self ):
        yawAngleError = -self.yawController.desiredYawAngle \
            + self.playerCompass.pose.pyaw
            
        # normalise the error:        
        while yawAngleError >= math.pi:
            yawAngleError -= 2*math.pi
        while yawAngleError < -math.pi:
            yawAngleError += 2*math.pi
            
        return ( abs( yawAngleError ) < abs( self.yawEpsilon ) )
        
    #---------------------------------------------------------------------------
    def atDesiredDepth( self ):
        
        if self.depthControlDisabled:
            depth = self.playerDepthSensor.pos
            
            if self.logger != None:
                #self.logger.logAction( -1.0, -1.0, depth, 
                #    "Using open loop depth control. Assuming depth reached..." )
                self.logger.logMsg( "Using open loop depth control. Assuming depth reached..." )
            return True
 
        depthError = self.depthController.desiredDepth - self.playerDepthSensor.pos
        
        return ( abs( depthError ) < abs( self.depthEpsilon ) )

    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self, linearSpeed ):
        
        MAX_UPDATES_PER_SECOND = 20.0
        TIME_BETWEEN_UPDATES = 1.0 / MAX_UPDATES_PER_SECOND
        
        curTime = time.time()
        if curTime - self.lastTime > TIME_BETWEEN_UPDATES:
            
            self.depthController.update()
            dSpeed = -self.depthController.depthSpeed                # m/s
            
            self.pitchController.update()  
            pSpeed = self.pitchController.pitchSpeed                # rad/s
            
            self.yawController.update()  
            ySpeed = self.yawController.yawSpeed                      # rad/s

            motorControl = (self.leftMotorUncontrolled << 3) \
                | (self.rightMotorUncontrolled << 2) \
                | (self.frontMotorUncontrolled << 1) \
                | self.backMotorUncontrolled

            # Add in some protection for the depth sensor crashing
            depth = self.playerDepthSensor.pos
            if depth == self.lastDepth:
                self.numIdenticalDepthReadings += 1
            else:
                self.numIdenticalDepthReadings = 0
                self.lastDepth = depth
                self.depthControlDisabled = False
                
            if not self.depthControlDisabled:
                if self.numIdenticalDepthReadings >= 40:
                    
                    if self.logger != None:
                        #self.logger.logAction( -1.0, -1.0, depth, 
                        #    "The depth sensor seems to have failed. Attempting open loop" )
                        self.logger.logMsg( "The depth sensor seems to have failed. Attempting open loop" )
                    self.depthControlDisabled = True

            if self.depthControlDisabled:
                dSpeed = -0.8
            
            #------------ Send the new speeds to player ----------#
            
            self.playerPos3D.set_velocity( linearSpeed, 0.0, dSpeed, # x, y, z
                                           0.0, pSpeed, ySpeed, # roll, pitch, yaw
                                           motorControl )   # State
            if self.playerSimPos3D != None:
                self.playerSimPos3D.set_velocity( linearSpeed, 0.0, dSpeed, # x, y, z
                                                  0.0, pSpeed, ySpeed, # roll, pitch, yaw
                                                  motorControl )   # State
            
            self.lastTime = curTime     
