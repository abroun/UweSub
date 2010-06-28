#-------------------------------------------------------------------------------
# A controller for setting the pitch angle of the AUV using a compass for feedback
#-------------------------------------------------------------------------------

import math

#-------------------------------------------------------------------------------
class PitchControl:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerSimPos3D = None ):
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerSimPos3D = playerSimPos3D
        
        # No desired angle to begin with so that the AUV doesn't just spin
        self.desiredPitchAngle = None
        # Pitch angle PID loop variables:
        self.pitchiState = 0.0
        self.lastPitchAngleError = 0.0
        self.pitchpTerm = 0.0
        self.pitchiTerm = 0.0
        self.pitchdTerm = 0.0
        # output of the pid:
        self.pitchSpeed = 0.0
        # control gains
        self.Kp = None
        self.Ki = None
        self.Kd = None
        self.iMax = None
        self.iMin = None

    #---------------------------------------------------------------------------
    def setPitchGains( self,  Kp, Ki, iMin, iMax, Kd  ):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = iMin
        self.iMax = iMax
        self.iMin = Kd
        
    #---------------------------------------------------------------------------
    def setDesiredPitchAngle( self, pitchAngle ):
        self.desiredPitchAngle = pitchAngle     # rad

    #----------------------Updates the control loop------------------------------
    def update( self ):
        
        if self.Kp == None:
            self.Kp = 3.0
        if self.Ki == None:
            self.Ki = 0.0
        if self.iMin == None:
            self.iMin = -1.57
        if self.iMax == None:
            self.iMax = 1.57
        if self.Kd == None:
            self.Kd = 0.0
        
        # Feedback from the Compass
        radCompassPitchAngle = self.playerCompass.pose.ppitch
        
        if self.desiredPitchAngle == None:
            # Cope with the case where DesiredPitchAngle is not set
            self.desiredPitchAngle = radCompassPitchAngle
              
        # 0 < angle < 2*pi
        while radCompassPitchAngle >= 2*math.pi:
            radCompassPitchAngle -= 2*math.pi

        #--------------------- PID loop ---------------------#

        # Proportional
        pitchAngleError = -self.desiredPitchAngle + radCompassPitchAngle    # rad
        #print pitchAngleError
        self.pitchpTerm = Kp*pitchAngleError
        
        # Integral
        self.pitchiState += pitchAngleError
        
        # Integral wind-up
        if self.pitchiState > iMax:
            self.pitchiState = iMax
        elif self.pitchiState < iMin:
            self.pitchiState = iMin
        self.pitchiTerm = Ki*self.pitchiState

        # Derivative
        pitchdState = pitchAngleError - self.lastPitchAngleError
        self.pitchdTerm = Kd*pitchdState
        self.lastPitchAngleError = pitchAngleError

        self.pitchSpeed = self.pitchpTerm + self.pitchiTerm + self.pitchdTerm    # rad/s
        
        #print "accumulating error ="
        #print self.pitchiState
