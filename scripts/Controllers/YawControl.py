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
    
    #---------------------------------------------------------------------------
    def setDesiredAngle( self, angle ):
        self.desiredAngle = angle
    
    #---------------------------------------------------------------------------
    # Updates the control loop and sends commands down to the position3D
    # interfaces if needed.
    def update( self ):
        
        Kp = 1.0
        Ki = 1.0
        Kd = 1.0
        iMax = 360
        iMin = -360
        lastAngleError = 0
        
        compassAngle = self.playerCompass.pose.pyaw
        if self.desiredAngle == None:
            # Cope with the case where DesiredAngle is not set
            self.desiredAngle = compassAngle
        
        linearSpeed = 0.0        # m/s
        print "control is called"
        #---------------------------------------------------------------------------
        # pidLoop for angular position
       # loopFlag = True
            
        #while loopFlag:
            #loopFlag = False
            #angleError = self.desiredAngle - compassAngle
            #pTerm = Kp*angleError
        
            #iState +=angleError
            #if iState > iMax:
                #iState = iMax
            #elif iState < iMin:
                #iState = iMin
            #iTerm = Ki*iState
        
            #dState = angleError - lastAngleError
            #dTerm = Kd*dState
            #lastAngleError = angleError
        
         #   angularSpeed = pTerm + iTerm + dTerm
        angularSpeed = 0.0
         
        depthSpeed = 0.0
            
        # Send the new speed to player
        self.playerPos3D.set_velocity( linearSpeed, 0.0, depthSpeed, # x, y, z
                                       0.0, 0.0, angularSpeed, # roll, pitch, yaw
                                       0 )   # State
                    
        if self.playerSimPos3D != None:
            self.playerSimPos3D.set_velocity( linearSpeed, 0.0, 0.0, # x, y, z
                                              0.0, 0.0, angularSpeed, # roll, pitch, yaw
                                              0 )   # State

        