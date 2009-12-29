import copy
import os
import yaml

KEYFRAME_TYPE_NONE = "None"
KEYFRAME_TYPE_INVISIBLE = "Invisible"
KEYFRAME_TYPE_VISIBLE = "Visible"
KEYFRAME_TYPE_LIST = [ KEYFRAME_TYPE_NONE, KEYFRAME_TYPE_INVISIBLE, KEYFRAME_TYPE_VISIBLE ]

#-------------------------------------------------------------------------------
class KeyFrame( yaml.YAMLObject ):

    yaml_tag = u'!KeyFrame'


    def __init__( self, type, centreX, centreY, radius ):
        self.type = type
        self.centreX = centreX
        self.centreY = centreY
        self.radius = radius
        
#-------------------------------------------------------------------------------
class BuoyData:

    def __init__( self, visible, centreX, centreY, radius ):
        self.visible = visible
        self.centreX = centreX
        self.centreY = centreY
        self.radius = radius
        
#-------------------------------------------------------------------------------
class Data:
    
    #---------------------------------------------------------------------------
    def __init__( self ):
        self.keyFrames = {}

    #---------------------------------------------------------------------------
    def clearKeyFrames( self ):
        self.keyFrames = {}

    #---------------------------------------------------------------------------
    def loadKeyFramesFromFile( self, keyFrameFilename ):
        if os.path.exists( keyFrameFilename ):
    
            keyFrameFile = file( keyFrameFilename, "r" )
            self.keyFrames = yaml.load( keyFrameFile )
            keyFrameFile.close()
    
    #---------------------------------------------------------------------------
    def saveKeyFramesToFile( self, keyFrameFilename ):
        saveFile = file( keyFrameFilename, "w" )
        yaml.dump( self.keyFrames, saveFile )
        saveFile.close()
        
    #---------------------------------------------------------------------------
    def getKeyFrameType( self, frameIdx ):
    
        keyFrameType = KEYFRAME_TYPE_NONE
    
        if frameIdx in self.keyFrames.keys():
            keyFrameType = self.keyFrames[ frameIdx ].type
        
        return keyFrameType
        
    #---------------------------------------------------------------------------
    def getBuoyData( self, frameIdx ):
        keyFrame = KeyFrame( KEYFRAME_TYPE_NONE, 0, 0, 0 )

        if frameIdx in self.keyFrames.keys():
            keyFrame = self.keyFrames[ frameIdx ]
        else:
            lastFrameIdx = -1

            sortedFrameIndices = self.keyFrames.keys()
            sortedFrameIndices.sort()
            for testFrameIdx in sortedFrameIndices:
                keyFrameDataFound = False

                if testFrameIdx < frameIdx:
                    lastFrameIdx = testFrameIdx
                elif testFrameIdx > frameIdx and -1 != lastFrameIdx:
                    keyFrame = copy.copy( self.keyFrames[ lastFrameIdx ] )
                    otherKeyFrame = self.keyFrames[ testFrameIdx ]

                    if keyFrame.type == KEYFRAME_TYPE_VISIBLE \
                        and otherKeyFrame.type == KEYFRAME_TYPE_VISIBLE:

                        # Lerp between the two frames
                        progress = float(frameIdx - lastFrameIdx)/float(testFrameIdx - lastFrameIdx)

                        keyFrame.centreX = keyFrame.centreX + progress*(otherKeyFrame.centreX - keyFrame.centreX)
                        keyFrame.centreY = keyFrame.centreY + progress*(otherKeyFrame.centreY - keyFrame.centreY)
                        keyFrame.radius = keyFrame.radius + progress*(otherKeyFrame.radius - keyFrame.radius)

                    keyFrameDataFound = True

                if keyFrameDataFound:
                    break

        # Translate the keyframe into buoy data
        buoyVisible = ( keyFrame.type == KEYFRAME_TYPE_VISIBLE )
        return BuoyData( buoyVisible, keyFrame.centreX, keyFrame.centreY, keyFrame.radius )
        

    