import yaml

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
    
    def __init__( self ):
        self.robotType = self.ROBOT_TYPE_REAL

        self.playerServerAddress = self.PLAYER_SERVER_ADDRESS
        self.playerServerPort = self.PLAYER_SERVER_PORT

        self.trackedHue = self.TRACKED_HUE
        self.maxAbsHueDiff = self.MAX_ABS_HUE_DIFF
        self.trackedSaturation = self.TRACKED_SATURATION
        self.maxAbsSaturationDiff = self.MAX_ABS_SATURATION_DIFF
        self.trackedValue = self.TRACKED_VALUE
        self.maxAbsValueDiff = self.MAX_ABS_VALUE_DIFF

        self.forwardSpeed = self.FORWARD_SPEED
        self.yawSpeed = self.YAW_SPEED
        self.screenRadiusOfCloseBuoy = self.SCREEN_RADIUS_OF_CLOSE_BUOY
        
        self.logFileDir = "${HOME}/dev/uwe/UweSub/logs"
        
        # Sonar
        self.safeSonarDepth = 1200 # We assume that pressure increases with depth
        
        # 