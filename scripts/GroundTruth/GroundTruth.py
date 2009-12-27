#! /usr/bin/python

#-------------------------------------------------------------------------------

# Create window
# Load video
# Display first frame

# Add buttons to go forwards and backwards a frame.
# display the current frame number in an editable text box next to a label with the total number of frames

# Laying out objects
# Create layout box
# Pack and show contents

# Let the user set the keyframe type (None, Invisible, Visible)
# For visible keyframes let the user set the x and y coordinates of the buoy
# and its radius

import copy
import cv
import pygtk
pygtk.require('2.0')
import gtk

KEYFRAME_TYPE_NONE = "None"
KEYFRAME_TYPE_INVISIBLE = "Invisible"
KEYFRAME_TYPE_VISIBLE = "Visible"
KEYFRAME_TYPE_LIST = [ KEYFRAME_TYPE_NONE, KEYFRAME_TYPE_INVISIBLE, KEYFRAME_TYPE_VISIBLE ]

class KeyFrame:
    def __init__( self, type, centreX, centreY, radius ):
        self.type = type
        self.centreX = centreX
        self.centreY = centreY
        self.radius = radius

def tryParseFloat( strFloat, alternative ):
    try:
        return float( strFloat )
    except:
        return alternative
        

class MainWindow:

    #---------------------------------------------------------------------------
    def __init__( self ):

        self.keyFrames = {}

        # Create a new window
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL)
    
        self.window.connect( "destroy", self.destroy )
    
        # Sets the border width of the window.
        self.window.set_border_width(10)

        # Layout box names have the format layoutBox_Level_Number
        layoutBox_A_0 = gtk.HBox()

        layoutBox_B_0 = gtk.VBox()

        # Load video and get information about the video file
        self.videoCapture = cv.CaptureFromFile( "../../data/buoy.avi" )
        self.numFrames = int( cv.GetCaptureProperty( self.videoCapture, cv.CV_CAP_PROP_FRAME_COUNT ) )
        
        # Create a textbox to show the current frame number
        self.tbxFrameNumber = gtk.Entry()
        #self.tbxFrameNumber.connect( "", self.onFrameNumberEdited )
        self.tbxFrameNumber.connect( "focus-out-event", self.onTbxFrameNumberFocusOut )
        self.tbxFrameNumber.connect( "key-press-event", self.onTbxFrameNumberKeyPressed )
        
        # Setup an image to show the current frame
        self.imgCurFrame = gtk.Image()
        layoutBox_B_0.pack_start( self.imgCurFrame )
        self.imgCurFrame.show()

        layoutBox_C_0 = gtk.HBox()

        # Add buttons to move back and forth through the video
        self.btnPrevFrame = gtk.Button( "<" )
        self.btnPrevFrame.connect( "clicked", self.gotoPrevFrame )
        layoutBox_C_0.pack_start( self.btnPrevFrame )
        self.btnPrevFrame.show()

        layoutBox_C_0.pack_start( self.tbxFrameNumber )
        self.tbxFrameNumber.show()

        self.btnNextFrame = gtk.Button( ">" )
        self.btnNextFrame.connect( "clicked", self.gotoNextFrame )
        layoutBox_C_0.pack_start( self.btnNextFrame )
        self.btnNextFrame.show()

        layoutBox_B_0.pack_start( layoutBox_C_0 )
        layoutBox_C_0.show()

        # Add the controls for editing keyframes
        layoutBox_B_1 = gtk.VBox()

        layoutBox_C_0 = gtk.HBox()
        lblKeyFrameType = gtk.Label( "KeyFrame Type:" )
        layoutBox_C_0.pack_start( lblKeyFrameType )
        lblKeyFrameType.show()
        self.cbxKeyFrameType = gtk.combo_box_new_text()
        
        for keyFrameType in KEYFRAME_TYPE_LIST:
            self.cbxKeyFrameType.append_text( keyFrameType )
        
        self.cbxKeyFrameType.connect( "changed", self.setupControlsForKeyFrame )
        layoutBox_C_0.pack_start( self.cbxKeyFrameType )
        self.cbxKeyFrameType.show()

        layoutBox_C_1 = gtk.HBox()
        lblKeyFrameCentreX = gtk.Label( "Centre X:" )
        layoutBox_C_1.pack_start( lblKeyFrameCentreX )
        lblKeyFrameCentreX.show()
        self.tbxKeyFrameCentreX = gtk.Entry()
        layoutBox_C_1.pack_start( self.tbxKeyFrameCentreX )
        self.tbxKeyFrameCentreX.connect( "focus-out-event", self.setKeyFrameDataFromControls )
        self.tbxKeyFrameCentreX.show()

        layoutBox_C_2 = gtk.HBox()
        lblKeyFrameCentreY = gtk.Label( "Centre Y:" )
        layoutBox_C_2.pack_start( lblKeyFrameCentreY )
        lblKeyFrameCentreY.show()
        self.tbxKeyFrameCentreY = gtk.Entry()
        layoutBox_C_2.pack_start( self.tbxKeyFrameCentreY )
        self.tbxKeyFrameCentreY.connect( "focus-out-event", self.setKeyFrameDataFromControls )
        self.tbxKeyFrameCentreY.show()

        layoutBox_C_3 = gtk.HBox()
        lblKeyFrameRadius = gtk.Label( "Radius:" )
        layoutBox_C_3.pack_start( lblKeyFrameRadius )
        lblKeyFrameRadius.show()
        self.tbxKeyFrameRadius = gtk.Entry()
        layoutBox_C_3.pack_start( self.tbxKeyFrameRadius )
        self.tbxKeyFrameRadius.connect( "focus-out-event", self.setKeyFrameDataFromControls )
        self.tbxKeyFrameRadius.show()

        layoutBox_B_1.pack_start( layoutBox_C_0, fill=False )
        layoutBox_C_0.show()
        layoutBox_B_1.pack_start( layoutBox_C_1, fill=False )
        layoutBox_C_1.show()
        layoutBox_B_1.pack_start( layoutBox_C_2, fill=False )
        layoutBox_C_2.show()
        layoutBox_B_1.pack_start( layoutBox_C_3, fill=False )
        layoutBox_C_3.show()

        layoutBox_A_0.pack_start( layoutBox_B_0 )
        layoutBox_B_0.show()
        layoutBox_A_0.pack_start( layoutBox_B_1 )
        layoutBox_B_1.show()

        self.setCurFrameIdx( 0 )
    
        # Finally add the root layout box and show the window
        self.window.add( layoutBox_A_0 )
        layoutBox_A_0.show()
        self.window.show()

    #---------------------------------------------------------------------------
    def setCurFrameIdx( self, frameIdx ):

        # Clip the frame index to a valid number
        if frameIdx < 0:
            frameIdx = 0
        elif frameIdx >= self.numFrames:
            frameIdx = self.numFrames - 1

        # Display the select frame
        self.curFrameIdx = frameIdx
        cv.SetCaptureProperty( self.videoCapture, cv.CV_CAP_PROP_POS_FRAMES, frameIdx )

        baseFrame = cv.QueryFrame( self.videoCapture )
        pythonFrame = cv.CloneImage( baseFrame )

        cv.CvtColor( pythonFrame, pythonFrame, cv.CV_BGR2RGB )
        pixBuf = gtk.gdk.pixbuf_new_from_data( 
            pythonFrame.tostring(), 
            gtk.gdk.COLORSPACE_RGB,
            False,
            pythonFrame.depth,
            pythonFrame.width,
            pythonFrame.height,
            pythonFrame.width*pythonFrame.nChannels )

        self.imgCurFrame.set_from_pixbuf( pixBuf )

        # Update the text-box that displays the current frame number
        self.tbxFrameNumber.set_text( str( frameIdx + 1 ) )

        # Display data for the current key-frame
        keyFrameData = self.getKeyFrameData( frameIdx )
        for keyFrameTypeIdx in range( len( KEYFRAME_TYPE_LIST ) ):
            if KEYFRAME_TYPE_LIST[ keyFrameTypeIdx ] == keyFrameData.type:
                self.cbxKeyFrameType.set_active( keyFrameTypeIdx )
                break

        self.tbxKeyFrameCentreX.set_text( str( keyFrameData.centreX ) )
        self.tbxKeyFrameCentreY.set_text( str( keyFrameData.centreY ) )
        self.tbxKeyFrameRadius.set_text( str( keyFrameData.radius ) )

    #---------------------------------------------------------------------------
    def setupControlsForKeyFrame( self, widget, data = None ):
        if self.cbxKeyFrameType.get_active_text() == KEYFRAME_TYPE_VISIBLE:
            self.tbxKeyFrameCentreX.set_sensitive( True )
            self.tbxKeyFrameCentreY.set_sensitive( True )
            self.tbxKeyFrameRadius.set_sensitive( True )
        else:
            self.tbxKeyFrameCentreX.set_sensitive( False )
            self.tbxKeyFrameCentreY.set_sensitive( False )
            self.tbxKeyFrameRadius.set_sensitive( False )

        #if self.cbxKeyFrameType.get_active_text() == KEYFRAME_TYPE_NONE:
        #    self.tbxKeyFrameCentreX.set_text( "" )
        #    self.tbxKeyFrameCentreY.set_text( "" )
        #    self.tbxKeyFrameRadius.set_text( "" )

    #---------------------------------------------------------------------------
    def setKeyFrameDataFromControls( self, widget, data = None ):
 
        centreX = tryParseFloat( self.tbxKeyFrameCentreX.get_text(), 0.0 )
        centreY = tryParseFloat( self.tbxKeyFrameCentreY.get_text(), 0.0 )
        radius = tryParseFloat( self.tbxKeyFrameRadius.get_text(), 0.0 )
        
        print "setting frame " + str( self.curFrameIdx )

        keyFrame = KeyFrame( self.cbxKeyFrameType.get_active_text(), centreX, centreY, radius )
        self.keyFrames[ self.curFrameIdx ] = keyFrame

    #---------------------------------------------------------------------------
    def gotoPrevFrame( self, widget, data = None ):
        self.setCurFrameIdx( self.curFrameIdx - 1 )

    #---------------------------------------------------------------------------
    def gotoNextFrame( self, widget, data = None ):
        self.setCurFrameIdx( self.curFrameIdx + 1 )

    #---------------------------------------------------------------------------
    def onTbxFrameNumberFocusOut( self, widget, data = None ):
        try:
            self.setCurFrameIdx( int( self.tbxFrameNumber.get_text() ) - 1 )
        except:
            pass    # Catch errors that may occur whilst parsing an integer

    #---------------------------------------------------------------------------
    def onTbxFrameNumberKeyPressed( self, widget, keyPressEvent ):
        if gtk.gdk.keyval_name( keyPressEvent.keyval ) == "Return":
            self.onTbxFrameNumberFocusOut( widget )

    #---------------------------------------------------------------------------
    def destroy( self, widget, data = None ):
        # Shutdown
        #if None != self.videoCapture: 
        #    cv.ReleaseCapture( self.videoCapture )
        gtk.main_quit()

    #---------------------------------------------------------------------------   
    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

    #---------------------------------------------------------------------------
    def getKeyFrameData( self, frameIdx ):
        keyFrame = KeyFrame( KEYFRAME_TYPE_NONE, 0, 0, 0 )

        print "Getting frame " + str( frameIdx )

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

                    keyFrame.type = KEYFRAME_TYPE_NONE
                    keyFrameDataFound = True

                if keyFrameDataFound:
                    break

        return keyFrame

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.main()


