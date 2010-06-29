#-------------------------------------------------------------------------------
# An arbitration mechanism for the control schemes
#-------------------------------------------------------------------------------

import math
import time

from Controllers import PitchControl
from Controllers import YawControl
from Controllers import DepthControl

#-------------------------------------------------------------------------------
class Arbitrator:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerDepthSensor, playerSimPos3D = None ):
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerDepthSensor = playerDepthSensor
        self.playerSimPos3D = playerSimPos3D
        
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
        
        self.lastTime = time.time()

    #---------------------------------------------------------------------------
    def setControlGains( self,  pitchKp, pitchKi, pitchiMin, pitchiMax, pitchKd,
                                  yawKp,   yawKi,   yawiMin,   yawiMax,    yawKd,
                                depthKp, depthKi, depthiMin, depthiMax, depthKd ):
        self.pitchController.setPitchGains( pitchKp, pitchKi, pitchiMin, pitchiMax, pitchKd )
        self.yawController.setYawGains( yawKp, yawKi, yawiMin, yawiMax, yawKd  )
        self.depthController.setDepthGains( depthKp, depthKi, depthiMin, depthiMax, depthKd  )

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
            
        return ( abs( yawAngleError ) < 5.0*math.pi/180.0 )
        
    #---------------------------------------------------------------------------
    def atDesiredDepth( self ):
        
        depthError = self.depthController.desiredDepth - self.playerDepthSensor.pos
        
        return ( abs( depthError ) < 0.1 )

    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self, linearSpeed ):
        
        MAX_UPDATES_PER_SECOND = 30.0
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

            #------------ Send the new speeds to player ----------#
            
            self.playerPos3D.set_velocity( linearSpeed, 0.0, dSpeed, # x, y, z
                                           0.0, pSpeed, ySpeed, # roll, pitch, yaw
                                           motorControl )   # State
            if self.playerSimPos3D != None:
                self.playerSimPos3D.set_velocity( linearSpeed, 0.0, dSpeed, # x, y, z
                                                  0.0, pSpeed, ySpeed, # roll, pitch, yaw
                                                  motorControl )   # State
            
            self.lastTime = curTime     
