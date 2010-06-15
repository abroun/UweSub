#-------------------------------------------------------------------------------
# A controller for setting the depth of the AUV using a depth sensor for feedback
#-------------------------------------------------------------------------------

import math
from Controllers import Arbitrator

#-------------------------------------------------------------------------------
class DepthControl:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerDepthSensor, playerSimPos3D = None ):
        
        self.playerPos3D = playerPos3D
        self.playerDepthSensor = playerDepthSensor
        self.playerSimPos3D = playerSimPos3D

        # No desired depth to begin with
        self.desiredDepth = None
        # Depth PID loop variables:
        self.depthiState = 0.0
        self.lastDepthError = 0.0
        self.depthpTerm = 0.0
        self.depthiTerm = 0.0
        self.depthdTerm = 0.0
        # output of the pid:
        self.depthSpeed = 0.0        

    #---------------------------------------------------------------------------
    def setDesiredDepth( self, depth ):
        self.desiredDepth = depth               # metres
    
    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self ):

        depthKp = 0.01
        depthKi = 0.008
        depthKd = 0.015
        depthiMax = 2.2
        depthiMin = -2.2
        
        # Feedback from the Depth Sensor
        depthSensorDepth = self.playerDepthSensor.pose.pz

        if self.desiredDepth == None:
            # Cope with the case where DesiredDepth is not set
            self.desiredDepth = depthSensorDepth

        #--------------------- PID loop ---------------------#

        # Proportional
        depthError = self.desiredDepth - depthSensorDepth    # rad
        #print angleError
        self.depthpTerm = depthKp*depthError
        
        # Integral
        self.depthiState += depthError
        
        # Integral wind-up
        if self.depthiState > depthiMax:
            self.depthiState = depthiMax
        elif self.depthiState < depthiMin:
            self.depthiState = depthiMin
        self.depthiTerm = depthKi*self.depthiState
        
        # Derivative
        depthdState = depthError - self.lastDepthError
        self.depthdTerm = depthKd*depthdState
        self.lastDepthError = depthError

        depthSpeed = self.depthpTerm + self.depthiTerm + self.depthdTerm    # rad/s
             
        #print "accumulating error ="
        #print self.depthiState
        
