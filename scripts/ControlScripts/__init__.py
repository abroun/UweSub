#-------------------------------------------------------------------------------
# Base class to use for writing control scripts for the submarine.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
class ControlScript:
    
    STATE_INVALID = "Invalid"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, 
        playerPos3D, playerCompass = None, 
        playerDepthSensor = None, playerSonar = None, 
        playerFrontCamera = None, playerBottomCamera = None ):
            
        self.logger = logger
        self.playerPos3D = playerPos3D
        self.playerCompass = playerCompass
        self.playerDepthSensor = playerDepthSensor
        self.playerSonar = playerSonar
        self.playerFrontCamera = playerFrontCamera
        self.playerBottomCamera = playerBottomCamera
        self.config = config
        
        self.state = self.STATE_INVALID
    
    #---------------------------------------------------------------------------
    def setState( self, state ):
        
        self.logger.logMsg( "Entering state - " + state )
        self.state = state
        
    #---------------------------------------------------------------------------
    # Override this routine with the functrionality of the control script
    def update():
        pass
        