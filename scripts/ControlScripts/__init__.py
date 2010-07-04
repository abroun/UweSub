#-------------------------------------------------------------------------------
# Base class to use for writing control scripts for the submarine.
#-------------------------------------------------------------------------------

import sys

# Add common packages directory to path
sys.path.append( "../" )
from SonarLocator import SonarLocator
import Maths

#-------------------------------------------------------------------------------
class ControlScript:
    
    STATE_INVALID = "Invalid"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, 
        playerPos3d, playerCompass = None, 
        playerDepthSensor = None, playerSonar = None, 
        playerFrontCamera = None, playerBottomCamera = None ):
            
        self.logger = logger
        self.playerPos3d = playerPos3d
        self.playerCompass = playerCompass
        self.playerDepthSensor = playerDepthSensor
        self.playerSonar = playerSonar
        self.playerFrontCamera = playerFrontCamera
        self.playerBottomCamera = playerBottomCamera
        self.config = config
        
        self.state = self.STATE_INVALID
        self.sonarLocator = SonarLocator( logger, 
            playerCompass, playerSonar, config=config )
        self.sonarLocator.setActive( False )    # Turn off by default
    
    #---------------------------------------------------------------------------
    def setSonarLocatorActive( self, active ):
        self.sonarLocator.setActive( active )
    
    #---------------------------------------------------------------------------
    def setState( self, state ):
        
        action = "Entering state - " + state
        
        self.logger.logMsg( action )
        self.logAction( action )
        self.state = state
        
    #---------------------------------------------------------------------------
    def logAction( self, action ):
        
        pos = self.sonarLocator.cornerPos
        if pos == None:
            x = -1.0
            y = -1.0
        else:
            x = pos.x
            y = pos.y
        
        z = self.playerDepthSensor.pos
        
        self.logger.logAction( x, y, z, action )
        
    #---------------------------------------------------------------------------
    # Override and then call this function in the control script
    def update( self ):
        self.sonarLocator.update()
        
        