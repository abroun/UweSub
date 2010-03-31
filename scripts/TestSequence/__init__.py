import os.path
import yaml

#-------------------------------------------------------------------------------
class TestSequence( yaml.YAMLObject ):

    yaml_tag = u'!TestSequence'

    #---------------------------------------------------------------------------
    def __init__( self ):
        self.fixedEntities = []
        self.frames = []

    #---------------------------------------------------------------------------
    def addFixedEntity( self, fixedEntity ):
        self.fixedEntities.append( fixedEntity )

    #---------------------------------------------------------------------------
    def addFrame( self, frameData ):
        self.frames.append( frameData )

#-------------------------------------------------------------------------------
class FixedEntityData( yaml.YAMLObject ):

    yaml_tag = u'!FixedEntityData'

    #---------------------------------------------------------------------------
    def __init__( self, name, x, y ):
        self.name = name
        self.x = x
        self.y = y

#-------------------------------------------------------------------------------
class FrameData( yaml.YAMLObject ):

    yaml_tag = u'!FrameData'

    #---------------------------------------------------------------------------
    def __init__( self, subX, subY, subYaw, timestamp, imageFilename ):
        self.subX = subX
        self.subY = subY
        self.subYaw = subYaw
        self.timestamp = timestamp
        self.imageFilename = imageFilename

#-------------------------------------------------------------------------------
def loadSequenceFromFile( filename ): 

    result = None

    if os.path.exists( filename ):
    
        sequenceFile = file( filename, "r" )
        result = yaml.load( sequenceFile )
        sequenceFile.close()

    return result