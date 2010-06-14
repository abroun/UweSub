#-------------------------------------------------------------------------------
# A controller for setting the angle of the AUV using a compass for feedback
#-------------------------------------------------------------------------------

import math

#-------------------------------------------------------------------------------
class YawControl:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerSimPos3D = None ):
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerSimPos3D = playerSimPos3D
        
        # No desired angle to begin with so that the AUV doesn't just spin round
        self.desiredPitchAngle = None
        # Pitch Angle PID loop variables
        self.pitchiState = 0.0
        self.lastPitchAngleError = 0.0
        self.pitchpTerm = 0.0
        self.pitchiTerm = 0.0
        self.pitchdTerm = 0.0

        # No desired angle to begin with so that the AUV doesn't just spin round
        self.desiredYawAngle = None
        # Yaw Angle PID loop variables
        self.yawiState = 0.0
        self.lastYawAngleError = 0.0
        self.yawpTerm = 0.0
        self.yawiTerm = 0.0
        self.yawdTerm = 0.0

         # No desired depth to begin with
        self.desiredDepth = None
        # Depth PID loop variables
        self.depthiState = 0.0
        self.lastDepthError = 0.0
        self.depthpTerm = 0.0
        self.depthiTerm = 0.0
        self.depthdTerm = 0.0

    #---------------------------------------------------------------------------
    def setDesiredState( self, pitchAngle, yawAngle, depth ):
        self.desiredPitchAngle = pitchAngle     # rad
        self.desiredYawAngle = yawAngle         # rad
        self.desiredDepth = depth               # metres
    
    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self, linearSpeed ):


        ###################### Pitch Angle ######################
        pitchKp = 0.01
        pitchKi = 0.008
        pitchKd = 0.015
        pitchiMax = 2.2
        pitchiMin = -2.2
        
        # Feedback from the Compass
        radCompassPitchYawAngle = self.playerCompass.pose.ppitch
        
        if self.desiredPitchAngle == None:
            # Cope with the case where DesiredPitchAngle is not set
            self.desiredPitchAngle = radCompassPitchAngle
              
        # 0 < angle < 2*pi
        while radCompassYawAngle >= 2*math.pi:
            radCompassYawAngle -= 2*math.pi

        #--------------------- PID loop ---------------------#

        # Proportional
        pitchAngleError = self.desiredPitchAngle - radCompassPitchAngle    # rad
        #print angleError
        self.pitchpTerm = pitchKp*pitchAngleError
        
        # Integral
        self.pitchiState += pitchAngleError
        
        # Integral wind-up
        if self.pitchiState > pitchiMax:
            self.pitchiState = pitchiMax
        elif self.pitchiState < pitchiMin:
            self.pitchiState = pitchiMin
        self.pitchiTerm = pitchKi*self.pitchiState
        
        # Derivative
        pitchdState = pitchAngleError - self.lastPitchAngleError
        self.pitchdTerm = pitchKd*pitchdState
        self.lastPitchAngleError = pitchAngleError

        pitchSpeed = self.pitchpTerm + self.pitchiTerm + self.pitchdTerm    # rad/s
        
        #print "accumulating error ="
        #print self.pitchiState
        
        
        ###################### Yaw Angle ######################
        yawKp = 0.01
        yawKi = 0.008
        yawKd = 0.015
        yawiMax = 2.2
        yawiMin = -2.2
        
        # Feedback from the Compass
        radCompassYawAngle = self.playerCompass.pose.pyaw

        if self.desiredYawAngle == None:
            # Cope with the case where DesiredYawAngle is not set
            self.desiredYawAngle = radCompassYawAngle
                
        # 0 < angle < 2*pi
        while radCompassYawAngle >= 2*math.pi:
            radCompassYawAngle -= 2*math.pi

        #--------------------- PID loop ---------------------#

        # Proportional
        yawAngleError = self.desiredYawAngle - radCompassYawAngle    # rad
        #print angleError
        self.yawpTerm = yawKp*yawAngleError
        
        # Integral
        self.yawiState += yawAngleError
        
        # Integral wind-up
        if self.yawiState > yawiMax:
            self.yawiState = yawiMax
        elif self.yawiState < yawiMin:
            self.yawiState = yawiMin
        self.yawiTerm = yawKi*self.yawiState
        
        # Derivative
        yawdState = yawAngleError - self.lastYawAngleError
        self.yawdTerm = yawKd*yawdState
        self.lastYawAngleError = yawAngleError

        yawSpeed = self.yawpTerm + self.yawiTerm + self.yawdTerm    # rad/s
             
        #print "accumulating error ="
        #print self.yawiState
        
        
        ####################### Depth #######################
        #depthKp = 0.01
        #depthKi = 0.008
        #depthKd = 0.015
        #depthiMax = 2.2
        #depthiMin = -2.2
        
        ## Feedback from the Compass
        #SensorDepth = self.playerPresSensor.pose.pz

        if self.desiredDepth == None:
            # Cope with the case where DesiredDepth is not set
            self.desiredDepth = SensorDepth
                

        #--------------------- PID loop ---------------------#

        # Proportional
        depthError = self.desiredDepth - SensorDepth    # rad
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
        

        ############# Send the new speeds to player #############
        
        
        self.playerPos3D.set_velocity( linearSpeed, 0.0, depthSpeed, # x, y, z
                                       0.0, pitchSpeed, yawSpeed, # roll, pitch, yaw
                                       0 )   # State
        if self.playerSimPos3D != None:
            self.playerSimPos3D.set_velocity( linearSpeed, 0.0, depthSpeed, # x, y, z
                                              0.0, pitchSpeed, yawSpeed, # roll, pitch, yaw
                                              0 )   # State
