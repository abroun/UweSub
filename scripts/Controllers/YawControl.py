#-------------------------------------------------------------------------------
# A controller for setting the yaw angle of the AUV using a compass for feedback
#-------------------------------------------------------------------------------

import math

#-------------------------------------------------------------------------------
class YawControl:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerSimPos3D = None ):
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerSimPos3D = playerSimPos3D

        # No desired angle to begin with so that the AUV doesn't just spin
        self.desiredYawAngle = None
        # Yaw angle PID loop variables:
        self.yawiState = 0.0
        self.lastYawAngleError = 0.0
        self.yawpTerm = 0.0
        self.yawiTerm = 0.0
        self.yawdTerm = 0.0
        # output of the pid:
        self.yawSpeed = 0.0        
        # control gains
        self.Kp = None
        self.Ki = None
        self.Kd = None
        self.iMax = None
        self.iMin = None

    #---------------------------------------------------------------------------
    def setYawGains( self,  Kp, Ki, iMin, iMax, Kd  ):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = iMin
        self.iMax = iMax
        self.iMin = Kd
                
    #---------------------------------------------------------------------------
    def setDesiredYawAngle( self, yawAngle ):
        self.desiredYawAngle = yawAngle         # rad
    
    #----------------------Updates the control loop------------------------------
    def update( self ):
        
        if self.Kp == None:
            self.Kp = 0.001
        if self.Ki == None:
            self.Ki = 0.0
        if self.iMin == None:
            self.iMin = -1.57
        if self.iMax == None:
            self.iMax = 1.57
        if self.Kd == None:
            self.Kd = 0.001

        # Feedback from the Compass
        radCompassYawAngle = self.playerCompass.pose.pyaw
        if self.desiredYawAngle == None:
            # Cope with the case where DesiredYawAngle is not set
            self.desiredYawAngle = radCompassYawAngle
                

        #--------------------- PID loop ---------------------#

        # Proportional
        
        yawAngleError = self.desiredYawAngle - radCompassYawAngle    # rad
        # normalise the error:        
        while yawAngleError >= math.pi:
            yawAngleError -= 2*math.pi
        while yawAngleError < -math.pi:
            yawAngleError += 2*math.pi
        #print "normalised yawAngleError =", yawAngleError

        self.yawpTerm = self.Kp*yawAngleError
        
        # Integral
        self.yawiState += yawAngleError
        
        # Integral wind-up
        if self.yawiState > self.iMax:
            self.yawiState = self.iMax
        elif self.yawiState < self.iMin:
            self.yawiState = self.iMin
        self.yawiTerm = self.Ki*self.yawiState
        
        # Derivative
        yawdState = yawAngleError + self.lastYawAngleError
        self.yawdTerm = self.Kd*yawdState
        self.lastYawAngleError = yawAngleError

        self.yawSpeed = self.yawpTerm + self.yawiTerm + self.yawdTerm    # rad/s
             
        #print "accumulating error ="
        #print self.yawiState
        