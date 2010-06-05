#-------------------------------------------------------------------------------
# A controller for setting the angle of the AUV using a compass for feedback
#-------------------------------------------------------------------------------

import math

#-------------------------------------------------------------------------------
class YawControl:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D, playerCompass, playerSimPos3D = None ):
        
        # No desired angle to begin with so that the AUV doesn't just spin round
        self.desiredAngle = None
        
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerSimPos3D = playerSimPos3D
        
        self.iState = 0.0
        self.lastAngleError = 0.0
    
    #---------------------------------------------------------------------------
    def setDesiredAngle( self, angle ):
        self.desiredAngle = angle   #rad
    
    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self, linearSpeed, depthSpeed ):

        Kp = 2.0
        Ki = 0.0
        Kd = 5.0
        iMax = math.pi
        iMin = -math.pi
        
        if self.desiredAngle == None:
            # Cope with the case where DesiredAngle is not set
            self.desiredAngle = radCompassAngle
                
        # Feedback from the Compass
        radCompassAngle = self.playerCompass.pose.pyaw

        #---------------------------------------------------------------------------
        # PID loop

        # Proportional
        angleError = self.desiredAngle - radCompassAngle
        #print angleError
        pTerm = Kp*angleError
        
        # Integral
        self.iState +=angleError
        
        print "accumulating error ="
        print self.iState
        
        # Integral wind-up
        if self.iState > iMax:
            self.iState = iMax
        elif self.iState < iMin:
            self.iState = iMin
        iTerm = Ki*self.iState
        
        # Derivative
        dState = angleError - self.lastAngleError
        dTerm = Kd*dState
        self.lastAngleError = angleError
    
        angularSpeed = pTerm + iTerm + dTerm
        
        # Send the new speed to player
        self.playerPos3D.set_velocity( linearSpeed, 0.0, depthSpeed, # x, y, z
                                       0.0, 0.0, angularSpeed, # roll, pitch, yaw
                                       0 )   # State
        if self.playerSimPos3D != None:
            self.playerSimPos3D.set_velocity( linearSpeed, 0.0, depthSpeed, # x, y, z
                                              0.0, 0.0, angularSpeed, # roll, pitch, yaw
                                              0 )   # State
