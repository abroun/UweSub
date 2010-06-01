#-------------------------------------------------------------------------------
# A controller for setting the angle of the AUV using a compass for feedback
#-------------------------------------------------------------------------------

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
        
        PROPORTIONAL_GAIN = 1.0
        
        compassAngle = self.playerCompass.pose.pyaw
        if self.desiredAngle == None:
            # Cope with the case where setDesiredAngle
            self.desiredAngle = compassAngle
        
        # Work out what we should set the linear and angular speed to
        angleError = self.desiredAngle - compassAngle
        
        linearSpeed = 0.0                              # Metres per second
        angularSpeed = PROPORTIONAL_GAIN*angleError    # Radians per second
        
        # Send the new speed to player
        self.playerPos3D.set_velocity( 
            linearSpeed, 0.0, 0.0, # x, y, z
            0.0, 0.0, angularSpeed, # roll, pitch, yaw
            0 )   # State
                    
        if self.playerSimPos3D != None:
            self.playerSimPos3D.set_velocity( 
                linearSpeed, 0.0, 0.0, # x, y, z
                0.0, 0.0, angularSpeed, # roll, pitch, yaw
                0 )   # State

        