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


            #------------ Send the new speeds to player ----------#
            
            self.playerPos3D.set_velocity( linearSpeed, 0.0, dSpeed, # x, y, z
                                           0.0, pSpeed, ySpeed, # roll, pitch, yaw
                                           0 )   # State
            if self.playerSimPos3D != None:
                self.playerSimPos3D.set_velocity( linearSpeed, 0.0, dSpeed, # x, y, z
                                                  0.0, pSpeed, ySpeed, # roll, pitch, yaw
                                                  0 )   # State
            
            self.lastTime = curTime     
