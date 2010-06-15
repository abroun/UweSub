#-------------------------------------------------------------------------------
# A controller for setting the yaw angle of the AUV using a compass for feedback
#-------------------------------------------------------------------------------

import math
from Controllers import Arbitrator
#-------------------------------------------------------------------------------
class YawControl:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerSimPos3D = None ):
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerSimPos3D = playerSimPos3D

        # No desired angle to begin with so that the AUV doesn't just spin round
        self.desiredYawAngle = None
        # Yaw angle PID loop variables:
        self.yawiState = 0.0
        self.lastYawAngleError = 0.0
        self.yawpTerm = 0.0
        self.yawiTerm = 0.0
        self.yawdTerm = 0.0
        # output of the pid:
        self.yawSpeed = 0.0        

    #---------------------------------------------------------------------------
    def setDesiredYawAngle( self, yawAngle ):
        self.desiredYawAngle = yawAngle         # rad
    
    #----------------------Updates the control loop------------------------------
    def update( self, linearSpeed ):

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
        