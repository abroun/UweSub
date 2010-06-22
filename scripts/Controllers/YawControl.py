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

    #---------------------------------------------------------------------------
    def setDesiredYawAngle( self, yawAngle ):
        self.desiredYawAngle = yawAngle         # rad
    
    #----------------------Updates the control loop------------------------------
    def update( self ):

        Kp = 0.01
        Ki = 0.00
        Kd = 0.015
        iMax = 1.57
        iMin = -1.57
        
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
        #print yawAngleError
        self.yawpTerm = Kp*yawAngleError
        
        # Integral
        self.yawiState += yawAngleError
        
        # Integral wind-up
        if self.yawiState > iMax:
            self.yawiState = iMax
        elif self.yawiState < iMin:
            self.yawiState = iMin
        self.yawiTerm = Ki*self.yawiState
        
        # Derivative
        yawdState = yawAngleError - self.lastYawAngleError
        self.yawdTerm = Kd*yawdState
        self.lastYawAngleError = yawAngleError

        self.yawSpeed = self.yawpTerm + self.yawiTerm + self.yawdTerm    # rad/s
             
        #print "accumulating error ="
        #print self.yawiState
        