#-------------------------------------------------------------------------------
# A controller for setting the pitch angle of the AUV using a compass for feedback
#-------------------------------------------------------------------------------

import math
from Controllers import Arbitrator

#-------------------------------------------------------------------------------
class PitchControl:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerSimPos3D = None ):
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerSimPos3D = playerSimPos3D
        
        # No desired angle to begin with so that the AUV doesn't just spin round
        self.desiredPitchAngle = None
        # Pitch angle PID loop variables:
        self.pitchiState = 0.0
        self.lastPitchAngleError = 0.0
        self.pitchpTerm = 0.0
        self.pitchiTerm = 0.0
        self.pitchdTerm = 0.0
        # output of the pid:
        self.pitchSpeed = 0.0

    #---------------------------------------------------------------------------
    def setDesiredState( self, pitchAngle, yawAngle, depth ):
        self.desiredPitchAngle = pitchAngle     # rad
        self.desiredYawAngle = yawAngle         # rad
        self.desiredDepth = depth               # metres
    
    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self, linearSpeed ):


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
