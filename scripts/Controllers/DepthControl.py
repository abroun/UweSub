#-------------------------------------------------------------------------------
# A controller for setting the depth of the AUV using a depth sensor for feedback
#-------------------------------------------------------------------------------

import math

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
        self.lastDepthSpeed = 0.0
        self.errorFlag = 0.0
        self.depthSpeed = 0.0
        self.depthpTerm = 0.0
        self.depthiTerm = 0.0
        self.depthdTerm = 0.0
        # output of the pid:
        self.depthSpeed = 0.0
        # control gains
        self.Kp = None
        self.Ki = None
        self.Kd = None
        self.iMax = None
        self.iMin = None        

    #---------------------------------------------------------------------------
    def setDepthGains( self,  Kp, Ki, iMin, iMax, Kd  ):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.iMax = iMax
        self.iMin = iMin
        
    #---------------------------------------------------------------------------
    def setDesiredDepth( self, depth ):
        self.desiredDepth = depth               # metres
    
    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self ):
        
        if self.Kp == None:
            self.Kp = 0.3
        if self.Ki == None:
            self.Ki = 0.0
        if self.iMin == None:
            self.iMin = -1.57
        if self.iMax == None:
            self.iMax = 1.57
        if self.Kd == None:
            self.Kd = 0.0

        # Feedback from the Depth Sensor
        depthSensorDepth = self.playerDepthSensor.pos
        
        if self.desiredDepth == None:
            # Cope with the case where DesiredDepth is not set
            self.desiredDepth = depthSensorDepth

        #--------------------- PID loop ---------------------#

        # Proportional
        depthError = self.desiredDepth - depthSensorDepth    # rad
        if depthError > 0.05 or depthError < -0.05:
            self.errorFlag = 0.0
        #print depthError
        self.depthpTerm = self.Kp*depthError
        
        # Integral
        self.depthiState += depthError
        
        # Integral wind-up
        if self.depthiState > self.iMax:
            self.depthiState = self.iMax
        elif self.depthiState < self.iMin:
            self.depthiState = self.iMin
        self.depthiTerm = self.Ki*self.depthiState
        
        # Derivative
        depthdState = depthError - self.lastDepthError
        self.depthdTerm = self.Kd*depthdState
        self.lastDepthError = depthError
        
        self.depthSpeed = self.depthpTerm + self.depthiTerm + self.depthdTerm    # rad/s
        if (depthError < 0.05 or depthError < -0.05) and self.errorFlag == 0.0:
            self.lastDepthSpeed = self.depthSpeed
            self.errorFlag = 1.0
        
        if (depthError < 0.05 or depthError < -0.05) and self.errorFlag == 1.0:
            self.depthSpeed = self.lastDepthSpeed
        
        #print "depthError  =", depthError
        #print "depthSpeed  =", self.depthSpeed
        