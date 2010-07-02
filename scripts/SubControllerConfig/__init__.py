import yaml
import sys

# Add common packages directory to path
sys.path.append( "../" )
import Maths

#-------------------------------------------------------------------------------
class SubControllerConfig( yaml.YAMLObject ):

    yaml_tag = u'!SubControllerConfig'

    ROBOT_TYPE_REAL = "Real"
    ROBOT_TYPE_SIM = "Sim"

    PLAYER_SERVER_ADDRESS = 'localhost'
    PLAYER_SERVER_PORT = 6665
    
    TRACKED_HUE = 22.0
    MAX_ABS_HUE_DIFF = 6.0
    TRACKED_SATURATION = 70.0
    MAX_ABS_SATURATION_DIFF = 5.0
    TRACKED_VALUE = 60.0
    MAX_ABS_VALUE_DIFF = 15.0

    FORWARD_SPEED = 1.0
    YAW_SPEED = 0.3
    SCREEN_RADIUS_OF_CLOSE_BUOY = 0.2
    
    #---------------------------------------------------------------------------
    def __init__( self ):
        self.addUnsetVariables()
        
    #---------------------------------------------------------------------------
    def addUnsetVariables( self ):
        
        setVariables = dir( self )
        
        if not "robotType" in setVariables:
            self.robotType = self.ROBOT_TYPE_REAL

        if not "playerServerAddress" in setVariables:
            self.playerServerAddress = self.PLAYER_SERVER_ADDRESS
        
        if not "playerServerPort" in setVariables:
            self.playerServerPort = self.PLAYER_SERVER_PORT

        if not "trackedHue" in setVariables:
            self.trackedHue = self.TRACKED_HUE
            
        if not "maxAbsHueDiff" in setVariables:
            self.maxAbsHueDiff = self.MAX_ABS_HUE_DIFF
            
        if not "trackedSaturation" in setVariables:
            self.trackedSaturation = self.TRACKED_SATURATION
        
        if not "maxAbsSaturationDiff" in setVariables:
            self.maxAbsSaturationDiff = self.MAX_ABS_SATURATION_DIFF
            
        if not "trackedValue" in setVariables:
            self.trackedValue = self.TRACKED_VALUE
        
        if not "maxAbsValueDiff" in setVariables:
            self.maxAbsValueDiff = self.MAX_ABS_VALUE_DIFF

        if not "forwardSpeed" in setVariables:
            self.forwardSpeed = self.FORWARD_SPEED
        
        if not "yawSpeed" in setVariables:
            self.yawSpeed = self.YAW_SPEED
        
        if not "screenRadiusOfCloseBuoy" in setVariables:
            self.screenRadiusOfCloseBuoy = self.SCREEN_RADIUS_OF_CLOSE_BUOY
        
        if not "logFileDir" in setVariables:
            self.logFileDir = "${HOME}/dev/uwe/UweSub/logs"
        
        if not "sonarImagesDir" in setVariables:
            self.sonarImagesDir = "${HOME}/dev/uwe/UweSub/logs/sonar"
        
        if not "cameraImagesDir" in setVariables:
            self.cameraImagesDir = "${HOME}/dev/uwe/UweSub/logs/camera"
        
        # Sonar
        if not "safeSonarDepth" in setVariables:
            self.safeSonarDepth = 50 # We assume that pressure increases with depth
        
        if not "sonarMaxTimeBetweenScans" in setVariables:
            self.sonarMaxTimeBetweenScans = 30.0
        
        if not "sonarNumFailedScansBetweenReboots" in setVariables:
            self.sonarNumFailedScansBetweenReboots = 2
        
        # Image Capture Script
        if not "IC_Script_sonarGain" in setVariables:
            self.IC_Script_sonarGain = 0.1
        
        if not "IC_Script_sonarRange" in setVariables:
            self.IC_Script_sonarRange = 70
        
        if not "IC_Script_sonarNumBins" in setVariables:
            self.IC_Script_sonarNumBins = 300
        
        if not "IC_Script_sonarScanStartAngle" in setVariables:
            self.IC_Script_sonarScanStartAngle = Maths.degToRad( 270.0 )
        
        if not "IC_Script_sonarScanEndAngle" in setVariables:
            self.IC_Script_sonarScanEndAngle = Maths.degToRad( 90.0 )
        
        if not "IC_Script_numImagesSavedPerSecond" in setVariables:
            self.IC_Script_numImagesSavedPerSecond = 1.0
        
        if not "IC_Script_enableCamera" in setVariables:
            self.IC_Script_enableCamera = True
        
        if not "IC_Script_enableSonar" in setVariables:
            self.IC_Script_enableSonar = False
        
        