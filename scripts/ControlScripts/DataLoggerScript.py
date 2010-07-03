#-------------------------------------------------------------------------------
# Simple script for logging readings from the sensors
#-------------------------------------------------------------------------------

import sys
import time
import math
import string
import os
from datetime import datetime
import cv
import playerc

from ControlScripts import ControlScript

# Add common packages directory to path
sys.path.append( "../" )
import Maths

#-------------------------------------------------------------------------------
class DataLoggerScript( ControlScript ):
    
    STATE_GATHERING_DATA = "Gathering Data"
    
    NUM_DATA_LOGS_PER_SECOND = 10 # Keep logs fairly low to avoid spamming the file
    TIME_BETWEEN_DATA_LOGS = 1.0 / NUM_DATA_LOGS_PER_SECOND
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3d, playerDepthSensor, playerCompass ):
        
        ControlScript.__init__( self, config, logger, 
            playerPos3d, playerCompass = playerCompass, 
            playerDepthSensor = playerDepthSensor )
            
        self.setState( self.STATE_GATHERING_DATA )
        self.lastLogTime = 0.0
        
    #---------------------------------------------------------------------------
    def update( self ):
        
        curTime = time.time()
        
        if self.state == self.STATE_GATHERING_DATA:

            if curTime - self.lastLogTime >= self.TIME_BETWEEN_DATA_LOGS:
                depth = self.playerDepthSensor.pos
                yaw = self.playerCompass.pose.pyaw
                pitch = self.playerCompass.pose.ppitch
                roll = self.playerCompass.pose.proll
                self.logger.logMsg( "DataLogger: Depth: {0}, Yaw: {1:2.3f}, Pitch: {2:2.3f}, Roll: {3:2.3f}".format(
                    depth, Maths.radToDeg( yaw ), Maths.radToDeg( pitch ), Maths.radToDeg( roll ) ) )
                
                self.lastLogTime = curTime
