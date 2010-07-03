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
        
        if not "IC_Script_sonarScanStartAngleDegrees" in setVariables:
            self.IC_Script_sonarScanStartAngleDegrees = 270.0
        
        if not "IC_Script_sonarScanEndAngleDegrees" in setVariables:
            self.IC_Script_sonarScanEndAngleDegrees = 90.0
        
        if not "IC_Script_numImagesSavedPerSecond" in setVariables:
            self.IC_Script_numImagesSavedPerSecond = 1.0
        
        if not "IC_Script_enableCamera" in setVariables:
            self.IC_Script_enableCamera = True
        
        if not "IC_Script_enableSonar" in setVariables:
            self.IC_Script_enableSonar = True
        
        # Control Gains
        if not "pitchKp" in setVariables:
            self.pitchKp = 3.0
        
        if not "pitchKi" in setVariables:
            self.pitchKi = 0.0
        
        if not "pitchiMin" in setVariables:
            self.pitchiMin=-1.57
        
        if not "pitchiMax" in setVariables:
            self.pitchiMax=1.57
        
        if not "pitchKd" in setVariables:
            self.pitchKd=0.0
        
        if not "yawKp" in setVariables:
            self.yawKp=-1.4
        
        if not "yawKi" in setVariables:
            self.yawKi=0.0
        
        if not "yawiMin" in setVariables:
            self.yawiMin=-1.57
        
        if not "yawiMax" in setVariables:
            self.yawiMax=-1.57
        
        if not "yawKd" in setVariables:
            self.yawKd=0.25
        
        if not "depthKp" in setVariables:
            self.depthKp=0.3
        
        if not "depthKi" in setVariables:
            self.depthKi=0.0
        
        if not "depthiMin" in setVariables:
            self.depthiMin=-1.57
        
        if not "depthiMax" in setVariables:
            self.depthiMax=1.57
        
        if not "depthKd" in setVariables:
            self.depthKd=0.0
            
        # Arbitrator epsilons
        if not "arbitratorDepthEpsilon" in setVariables:
            self.arbitratorDepthEpsilon = 10
        
        if not "arbitratorYawEpsilonDegrees" in setVariables:
            self.arbitratorYawEpsilonDegrees = 2.5
        
        # Qualifying run script
        if not "QR_runDepth" in setVariables:
            self.QR_runDepth = 5400
        
        if not "QR_forwardSpeed" in setVariables:
            self.QR_forwardSpeed = 0.8
        
        if not "QR_startDelayTime" in setVariables:
            self.QR_startDelayTime = 0.5*60.0
        
        if not "QR_moveForwardTime" in setVariables:
            self.QR_moveForwardTime = 2.0*60.0
        
        if not "QR_headingToGateDegrees" in setVariables:
            self.QR_headingToGateDegrees = 262.0
    
        if not "QR_useImageCapture" in setVariables:
            self.QR_useImageCapture = False
        
        
        