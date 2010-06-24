#-------------------------------------------------------------------------------
class KillMotors:
    
    #---------------------------------------------------------------------------
    def __init__( self, playerPos3D ):
        
        self.playerPos3D = playerPos3D

    #---------------------------------------------------------------------------
    def update( self ):
        
        #------------ Send zero to player ----------#
        self.playerPos3D.set_velocity( 0.0, 0.0, 0.0, # x, y, z
                                       0.0, 0.0, 0.0, # roll, pitch, yaw
                                       0 )   # State
