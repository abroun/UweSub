#-------------------------------------------------------------------------------
# Script for descending to a given depth whilst taking sonar scans
#-------------------------------------------------------------------------------

import sys
import time
import math

from ControlScripts import ControlScript

# Add common packages directory to path
sys.path.append( "../" )
from Controllers import Arbitrator
import Maths

#-------------------------------------------------------------------------------
class DepthTest( ControlScript ):
    
    STATE_DIVING = "Diving"
    STATE_PERFORMING_SCANS = "Performing Scans"
    STATE_SURFACING = "Surfacing"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3D, playerCompass, 
        playerDepthSensor, playerSonar = None ):
        
        ControlScript.__init__( self, config, logger, playerPos3D, playerCompass, 
            playerDepthSensor, playerSonar )
        
        self.scanDepth = -1.0   # TODO: Set from config file
        
        self.arbitrator = Arbitrator( playerPos3D, playerCompass, playerDepthSensor )
        self.arbitrator.setDesiredDepth( self.scanDepth )
        self.linearSpeed = 0.0
        self.setState( self.STATE_DIVING )
        self.driveTimer = time.time()
    
    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.state == self.STATE_DIVING:

            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredYaw( Maths.degToRad( 0.0 ) )
                self.setState( self.STATE_TURNING_TO_GATE_1 )
                
        elif self.state == self.STATE_SURFACING:
            
            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredDepth( self.scanDepth )
                self.setState( self.STATE_FINISHED )
            
        elif self.state == self.STATE_FINISHED:
            # Nothig to do
            pass
        else:
            self.logger.logError( "Unrecognised state - surfacing" )
            self.setState( self.STATE_SURFACING )
        
        self.arbitrator.update( self.linearSpeed )
        
