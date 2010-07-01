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
class ImageCaptureScript( ControlScript ):
    
    STATE_PERFORMING_SCANS = "Performing Scans"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3D, playerCompass, 
        playerDepthSensor, playerSonar = None ):
        
        ControlScript.__init__( self, config, logger, 
            playerPos3D, playerCompass, 
            playerDepthSensor, playerSonar )
        
        self.setState( self.STATE_PERFORMING_SCANS )
        self.lastCameraFrameTime = 0.0
    
    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.state == self.STATE_PERFORMING_SCANS:

            if self.arbitrator.atDesiredDepth():
                self.arbitrator.setDesiredYaw( Maths.degToRad( 0.0 ) )
                self.setState( self.STATE_TURNING_TO_GATE_1 )
                
        
        
