#-------------------------------------------------------------------------------
# An arbitration mechanism for the control schemes
#-------------------------------------------------------------------------------

import math

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
        
        self.pitchController = PitchControl( self.playerPos3d,
            self.playerCompass, self.playerSimPos3d )
        self.yawController = YawControl( self.playerPos3d,
            self.playerCompass, self.playerSimPos3d )
        self.depthController = DepthControl( self.playerPos3d,
            self.playerDepthSensor, self.playerSimPos3d )

    #---------------------------------------------------------------------------
    def setDesiredState( self, pitchAngle, yawAngle, depth ):        
        self.pitchController.setDesiredPitchAngle( pitchAngle )     # rad
        self.yawController.setDesiredYawAngle( yawAngle )           # rad
        self.depthController.setDesiredDepth( depth )               # m

    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self, linearSpeed ):
        
        pitchSpeed = self.pitchController.pitchSpeed                # rad/s
        yawSpeed = self.yawController.yawSpeed                      # rad/s
        depthSpeed = self.depthController.depthSpeed                # m/s


        #------------ Send the new speeds to player ----------#
        
        self.playerPos3D.set_velocity( linearSpeed, 0.0, depthSpeed, # x, y, z
                                       0.0, pitchSpeed, yawSpeed, # roll, pitch, yaw
                                       0 )   # State
        if self.playerSimPos3D != None:
            self.playerSimPos3D.set_velocity( linearSpeed, 0.0, depthSpeed, # x, y, z
                                              0.0, pitchSpeed, yawSpeed, # roll, pitch, yaw
                                              0 )   # State
