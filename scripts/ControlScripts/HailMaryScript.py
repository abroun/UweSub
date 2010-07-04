#-------------------------------------------------------------------------------
# Yay! Everything! All in one go with no real world testing! :D
#-------------------------------------------------------------------------------

import copy
import sys
import time
import math

from ControlScripts import ControlScript

# Add common packages directory to path
sys.path.append( "../" )
from Controllers import Arbitrator
from Controllers import KillMotors
from ImageCaptureScript import ImageCaptureScript
import Maths
import Profiling

#-------------------------------------------------------------------------------
class HailMaryScript( ControlScript ):
    
    STATE_WAITING_TO_START = "WaitingToStart"
    STATE_DIVING = "Diving"
    STATE_TURNING_TO_GATE_1 = "TurningToGate_1"
    STATE_DRIVING_THROUGH_GATE_1 = "DrivingThroughGate_1"
    STATE_DESCENDING_TO_PIPE = "DescendingToPipe"
    STATE_TURNING_TO_GATE_2 = "TurningToGate_2"
    STATE_SURVEYING_PIPE = "SurveyingPipe"
    STATE_RETURNING_TO_NORMAL_DEPTH = "ReturningToNormalDepth"
    STATE_TURNING_TO_WALL = "TurningToWall"
    STATE_APPROACHING_WALL = "ApproachingWall"
    STATE_SURVEYING_WALL = "SurveyingWall"
    STATE_TURNING_TO_HUNT_BUOY = "TurningToHuntBuoy"
    STATE_HUNTING_BUOY = "HuntingBuoy"
    STATE_RETURNING_TO_CENTRE = "ReturningToCentre"
    STATE_SURFACING = "Surfacing"
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logger, playerPos3d, playerCompass, 
        playerDepthSensor, playerSonar, playerFrontCamera ):
        
        ControlScript.__init__( self, config, logger, 
            playerPos3d=playerPos3d, playerCompass=playerCompass, 
            playerDepthSensor=playerDepthSensor, playerSonar=playerSonar, 
            playerFrontCamera=playerFrontCamera )
        
        self.NORMAL_DEPTH = self.config.HM_normalDepth
        self.PIPE_SURVEY_DEPTH = self.config.HM_pipeSurveyDepth
        self.FORWARD_SPEED = self.config.HM_forwardSpeed
        self.START_DELAY_TIME = self.config.HM_startDelayTime
        self.END_DELAY_TIME = self.config.HM_endDelayTime
        self.DRIVING_THROUGH_GATE_1_TIME = self.config.HM_drivingThroughGate_1_Time
        self.SURVEYING_PIPE_TIME = self.config.HM_surveyingPipeTime
        self.APPROACHING_WALL_TIME = self.config.HM_approachingWallTime
        self.SURVEYING_WALL_TIME = self.config.HM_surveyingWallTime
        self.MAX_HUNTING_BUOY_TIME = self.config.HM_maxHuntingBuoyTime
        self.RETURNING_TO_CENTRE_TIME = self.config.HM_returningToCentreTime
        self.NORTH_HEADING_DEGREES = self.config.HM_northHeadingDegrees
        self.EAST_HEADING_DEGREES = self.config.HM_eastHeadingDegrees
        self.SOUTH_HEADING_DEGREES = self.config.HM_southHeadingDegrees
        self.WEST_HEADING_DEGREES = self.config.HM_westHeadingDegrees
        
        # Configure the image capture script as we please
        imageCaptureConfig = copy.deepcopy( self.config )
        imageCaptureConfig.IC_Script_sonarGain = 0.3
        imageCaptureConfig.IC_Script_sonarRange = 25
        imageCaptureConfig.IC_Script_sonarNumBins = 300
        imageCaptureConfig.IC_Script_sonarScanStartAngleDegrees = 0.0
        imageCaptureConfig.IC_Script_sonarScanEndAngleDegrees = 350.0
        imageCaptureConfig.IC_Script_numImagesSavedPerSecond = 10.0
        imageCaptureConfig.IC_Script_enableCamera = True
        imageCaptureConfig.IC_Script_enableSonar = False
        
        self.imageCaptureScript = ImageCaptureScript( imageCaptureConfig, self.logger,
            self.playerPos3d, self.playerDepthSensor, self.playerSonar, self.playerFrontCamera )
        
        self.motorKiller = KillMotors( self.playerPos3d )
        
        # Setup the arbitrator
        self.arbitrator = Arbitrator( playerPos3d, playerCompass, playerDepthSensor, logger=logger )
        self.arbitrator.setDesiredPitch( Maths.degToRad( -4.0 ) )
        self.arbitrator.setControlGains(
            pitchKp=self.config.pitchKp, 
            pitchKi=self.config.pitchKi, pitchiMin=self.config.pitchiMin, pitchiMax=self.config.pitchiMax, 
            pitchKd=self.config.pitchKd,
            yawKp=self.config.yawKp, 
            yawKi=self.config.yawKi, yawiMin=self.config.yawiMin, yawiMax=self.config.yawiMax, 
            yawKd=self.config.yawKd,
            depthKp=self.config.depthKp, 
            depthKi=self.config.depthKi, depthiMin=self.config.depthiMin, depthiMax=self.config.depthiMax,
            depthKd=self.config.depthKd )
        self.arbitrator.setEpsilons( 
            self.config.arbitratorDepthEpsilon, 
            Maths.degToRad( self.config.arbitratorYawEpsilonDegrees ) )
        
        # Clear timer
        self.stateTimer = 0.0
        
        # Move into the first state
        self.setState( self.STATE_WAITING_TO_START )    
    
    #---------------------------------------------------------------------------
    def setState( self, newState ):
        
        self.exitState()
        
        if newState == self.STATE_WAITING_TO_START:
            
            self.linearSpeed = 0.0
            self.stateTimer = time.time()
            
        elif newState == self.STATE_DIVING:

            self.linearSpeed = 0.0
            self.logAction( "Descending to " + str( self.NORMAL_DEPTH ) )
            self.arbitrator.setDesiredDepth( self.NORMAL_DEPTH )

        elif newState == self.STATE_TURNING_TO_GATE_1:

            self.linearSpeed = 0.0
            self.arbitrator.setDesiredYaw( 
                Maths.degToRad( self.NORTH_HEADING_DEGREES ) )
            self.setSonarLocatorActive( True )
                        
        elif newState == self.STATE_DRIVING_THROUGH_GATE_1:
            
            self.linearSpeed = self.FORWARD_SPEED
            self.driveTimer = time.time()
    
        elif newState == self.STATE_DESCENDING_TO_PIPE:
            
            self.linearSpeed = 0.0
            self.logAction( "Descending to " + str( self.PIPE_SURVEY_DEPTH ) )
            self.arbitrator.setDesiredDepth( self.PIPE_SURVEY_DEPTH )
            
        elif newState == self.STATE_TURNING_TO_GATE_2:
            
            self.linearSpeed = 0.0
            self.arbitrator.setDesiredYaw( 
                Maths.degToRad( self.SOUTH_HEADING_DEGREES ) )
                
        elif newState == self.STATE_SURVEYING_PIPE:
            
            self.linearSpeed = self.FORWARD_SPEED
            self.driveTimer = time.time()
            
        elif newState == self.STATE_RETURNING_TO_NORMAL_DEPTH:
            
            self.linearSpeed = 0.0
            self.logAction( "Climbing to " + str( self.NORMAL_DEPTH ) )
            self.arbitrator.setDesiredDepth( self.NORMAL_DEPTH )
            
        elif newState == self.STATE_TURNING_TO_WALL:
            
            self.linearSpeed = 0.0
            self.arbitrator.setDesiredYaw( 
                Maths.degToRad( self.EAST_HEADING_DEGREES ) )
            
        elif newState == self.STATE_APPROACHING_WALL:
            
            self.linearSpeed = self.FORWARD_SPEED
            self.driveTimer = time.time()
            
        elif newState == self.STATE_SURVEYING_WALL:
            
            self.linearSpeed = 0.0
            self.stateTimer = time.time()
            self.setSonarLocatorActive( False )
            self.imageCaptureScript.config.IC_Script_enableSonar = True
            
        elif newState == self.STATE_TURNING_TO_HUNT_BUOY:
            
            self.linearSpeed = 0.0
            self.arbitrator.setDesiredYaw( 
                Maths.degToRad( self.WEST_HEADING_DEGREES ) )
            
        elif newState == self.STATE_HUNTING_BUOY:
    
            # Go, go, go!
            self.stateTimer = time.time()
            
        elif newState == self.STATE_RETURNING_TO_CENTRE:
    
            # Blast forward in hopeful direction
            self.linearSpeed = self.FORWARD_SPEED
            heading = ( self.WEST_HEADING_DEGREES + 45.0 )
            self.arbitrator.setDesiredYaw( 
                Maths.degToRad( heading ) )
    
        elif newState == self.STATE_SURFACING:
            
            self.linearSpeed = 0.0
            self.stateTimer = time.time()
            
        else:
            self.logger.logError( "Enter State - Unrecognised state - ({0})".format( self.state ) )
            return
        
        ControlScript.setState( self, newState )
    
    #---------------------------------------------------------------------------
    def exitState( self ):
        
        if self.state ==  self.STATE_INVALID:
            pass
        if self.state == self.STATE_WAITING_TO_START:
            pass
        elif self.state == self.STATE_DIVING:
            pass
        elif self.state == self.STATE_TURNING_TO_GATE_1:
            pass        
        elif self.state == self.STATE_DRIVING_THROUGH_GATE_1:
            pass
        elif self.state == self.STATE_DESCENDING_TO_PIPE:
            pass
        elif self.state == self.STATE_TURNING_TO_GATE_2:
            pass
        elif self.state == self.STATE_SURVEYING_PIPE:
            pass
        elif self.state == self.STATE_RETURNING_TO_NORMAL_DEPTH:
            pass
        elif self.state == self.STATE_TURNING_TO_WALL:
            pass
        elif self.state == self.STATE_APPROACHING_WALL:
            pass
        elif self.state == self.STATE_SURVEYING_WALL:
            
            self.imageCaptureScript.config.IC_Script_enableSonar = False
            self.setSonarLocatorActive( True )
        
        elif self.state == self.STATE_TURNING_TO_HUNT_BUOY:
            pass
        elif self.state == self.STATE_HUNTING_BUOY:
            pass
        elif self.state == self.STATE_RETURNING_TO_CENTRE:
            pass
        elif self.state == self.STATE_SURFACING:
            pass
        else:
            self.logger.logError( "Exit State - Unrecognised state - ({0})".format( self.state ) )
        
    #---------------------------------------------------------------------------
    @Profiling.printTiming
    def update( self ):
        
        curTime = time.time()
        
        ControlScript.update( self )
        
        if self.state != self.STATE_WAITING_TO_START:
            self.imageCaptureScript.update()
        
        if self.state == self.STATE_WAITING_TO_START:
            
            timeDiff = curTime - self.stateTimer
            print "timeDiff is", timeDiff, "delay is", self.START_DELAY_TIME
            
            if curTime - self.stateTimer >= self.START_DELAY_TIME:
                self.setState( self.STATE_DIVING )
            
        elif self.state == self.STATE_DIVING:

            if self.arbitrator.atDesiredDepth():
                self.setState( self.STATE_TURNING_TO_GATE_1 )
            
        elif self.state == self.STATE_TURNING_TO_GATE_1:
            
            if self.arbitrator.atDesiredYaw():
                self.setState( self.STATE_DRIVING_THROUGH_GATE_1 )
                        
        elif self.state == self.STATE_DRIVING_THROUGH_GATE_1:
            
            if curTime - self.driveTimer >= self.DRIVING_THROUGH_GATE_1_TIME:
                self.setState( self.STATE_DESCENDING_TO_PIPE )
                
        elif self.state == self.STATE_DESCENDING_TO_PIPE:
            
            if self.arbitrator.atDesiredDepth():
                self.setState( self.STATE_TURNING_TO_GATE_2 )
            
        elif self.state == self.STATE_TURNING_TO_GATE_2:
            
            if self.arbitrator.atDesiredYaw():
                self.setState( self.STATE_SURVEYING_PIPE )
        
        elif self.state == self.STATE_SURVEYING_PIPE:
        
            if curTime - self.driveTimer >= self.SURVEYING_PIPE_TIME:
                self.setState( self.STATE_RETURNING_TO_NORMAL_DEPTH )
                
        elif self.state == self.STATE_RETURNING_TO_NORMAL_DEPTH:
            
            if self.arbitrator.atDesiredDepth():
                self.setState( self.STATE_TURNING_TO_WALL )
                
        elif self.state == self.STATE_TURNING_TO_WALL:
            
            if self.arbitrator.atDesiredYaw():
                self.setState( self.STATE_APPROACHING_WALL )
        
        elif self.state == self.STATE_APPROACHING_WALL:
            
            if curTime - self.driveTimer >= self.APPROACHING_WALL_TIME:
                self.setState( self.STATE_SURVEYING_WALL )
                
        elif self.state == self.STATE_SURVEYING_WALL:
            
            if curTime - self.stateTimer >= self.SURVEYING_WALL_TIME:
                self.setState( self.STATE_TURNING_TO_HUNT_BUOY )
        
        elif self.state == self.STATE_TURNING_TO_HUNT_BUOY:
            
            if self.arbitrator.atDesiredYaw():
                self.setState( self.STATE_HUNTING_BUOY )
        
        elif self.state == self.STATE_HUNTING_BUOY:
            
            if curTime - self.stateTimer >= self.MAX_HUNTING_BUOY_TIME:
                self.setState( self.STATE_RETURNING_TO_CENTRE )
                
        elif self.state == self.STATE_RETURNING_TO_CENTRE:
            
            if curTime - self.stateTimer >= self.RETURNING_TO_CENTRE_TIME:
                self.setState( self.STATE_SURFACING )
        
        elif self.state == self.STATE_SURFACING:
            # Wait for a bit and then exit the program
            timeDiff = curTime - self.stateTimer    
            if timeDiff >= self.END_DELAY_TIME:
                sys.exit( 0 )   # Quit
            
        else:
            self.logger.logError( "Update - Unrecognised state - ({0})".format( self.state ) )
        
        if self.state == self.STATE_SURFACING:
            # Kill motors to come up and end mission
            self.motorKiller.update()
        else:
            self.arbitrator.update( self.linearSpeed )
        
