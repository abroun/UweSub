#! /usr/bin/python

#-------------------------------------------------------------------------------
# Simple program entering the ground truth information about buoy position
#-------------------------------------------------------------------------------

import cv
import pygtk
pygtk.require('2.0')
import gtk

import BuoyGroundTruth

#-------------------------------------------------------------------------------
def tryParseFloat( strFloat, alternative ):
    try:
        return float( strFloat )
    except:
        return alternative
        

#-------------------------------------------------------------------------------
class MainWindow:

    UI = '''
        <ui>
        <menubar name="MenuBar">
            <menu action="File">
                <menuitem action="ClearKeyFrames"/>
                <menuitem action="Save"/>
                <separator/>
                <menuitem action="Quit"/>
            </menu>
        </menubar>
        </ui>'''

    #---------------------------------------------------------------------------
    def __init__( self ):

        self.groundTruthData = BuoyGroundTruth.Data()
        self.loadKeyFrameDataFromFile()
        self.curFramePixBuf = None
        self.settingFrame = False

        # Create a new window
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL)
    
        self.window.connect( "destroy", self.destroy )
    
        # Sets the border width of the window.
        self.window.set_border_width(10)

        # Layout box names have the format layoutBox_Level_Number
        layoutBox_A_0 = gtk.VBox()
        
        # Add a menu
        uiManager = gtk.UIManager()
        accelGroup = uiManager.get_accel_group()
        self.window.add_accel_group( accelGroup )
        
        actionGroup = gtk.ActionGroup( "MenuActions" )

        # Create actions
        actionGroup.add_actions( 
            [ ( "Quit", gtk.STOCK_QUIT, None, "<Control>q", None, self.destroy ),
            ( "File", None, "_File" ),
            ( "ClearKeyFrames", None, "_Clear Key Frames", None, None, self.clearKeyFrames ),
            ( "Save", gtk.STOCK_SAVE, None, "<Control>s", None, self.saveKeyFrameDataToFile )] )
           
        uiManager.insert_action_group( actionGroup, 0 )
        
        # Setup and show the menu bar
        uiManager.add_ui_from_string( self.UI )
        menuBar = uiManager.get_widget( "/MenuBar" )
        layoutBox_A_0.pack_start( menuBar, False )
        menuBar.show()

        layoutBox_B_0 = gtk.HBox()
        layoutBox_C_0 = gtk.VBox()

        # Load video and get information about the video file
        self.videoCapture = cv.CaptureFromFile( "../data/buoy.avi" )
        self.numFrames = int( cv.GetCaptureProperty( self.videoCapture, cv.CV_CAP_PROP_FRAME_COUNT ) )
        self.frameWidth = int( cv.GetCaptureProperty( self.videoCapture, cv.CV_CAP_PROP_FRAME_WIDTH ) )
        self.frameHeight = int( cv.GetCaptureProperty( self.videoCapture, cv.CV_CAP_PROP_FRAME_HEIGHT ) )
             
        # Setup an drawing area to show the current frame
        self.dwgCurFrame = gtk.DrawingArea()
        self.dwgCurFrame.add_events( gtk.gdk.BUTTON_PRESS_MASK )
        self.dwgCurFrame.connect( "expose_event", self.onDwgCurFrameExpose )
        self.dwgCurFrame.connect( "button-press-event", self.onDwgCurFrameButtonPress )
        self.dwgCurFrame.set_size_request( self.frameWidth, self.frameHeight )
        layoutBox_C_0.pack_start( self.dwgCurFrame )
        self.dwgCurFrame.show()

        layoutBox_D_0 = gtk.HBox()

        # Add buttons to move back and forth through the video
        self.btnPrevFrame = gtk.Button( "<" )
        self.btnPrevFrame.connect( "clicked", self.gotoPrevFrame )
        layoutBox_D_0.pack_start( self.btnPrevFrame )
        self.btnPrevFrame.show()
        
        # Create a textbox to show the current frame number
        self.tbxFrameNumber = gtk.Entry()
        self.tbxFrameNumber.connect( "focus-out-event", self.onTbxFrameNumberFocusOut )
        self.tbxFrameNumber.connect( "key-press-event", self.onTbxFrameNumberKeyPressed )
        layoutBox_D_0.pack_start( self.tbxFrameNumber )
        self.tbxFrameNumber.show()
        
        lblFrameNumber = gtk.Label( " / " + str( self.numFrames ) )
        layoutBox_D_0.pack_start( lblFrameNumber )
        lblFrameNumber.show()

        self.btnNextFrame = gtk.Button( ">" )
        self.btnNextFrame.connect( "clicked", self.gotoNextFrame )
        layoutBox_D_0.pack_start( self.btnNextFrame )
        self.btnNextFrame.show()

        layoutBox_C_0.pack_start( layoutBox_D_0 )
        layoutBox_D_0.show()

        # Add the controls for editing keyframes
        layoutBox_C_1 = gtk.VBox()

        layoutBox_D_0 = gtk.HBox()
        lblKeyFrameType = gtk.Label( "KeyFrame Type:" )
        layoutBox_D_0.pack_start( lblKeyFrameType )
        lblKeyFrameType.show()
        self.cbxKeyFrameType = gtk.combo_box_new_text()
        
        for keyFrameType in BuoyGroundTruth.KEYFRAME_TYPE_LIST:
            self.cbxKeyFrameType.append_text( keyFrameType )
        
        self.cbxKeyFrameType.connect( "changed", self.setupControlsForKeyFrame )
        layoutBox_D_0.pack_start( self.cbxKeyFrameType )
        self.cbxKeyFrameType.show()

        self.chkBuoyVisible = gtk.CheckButton( "Buoy Visible" )
        self.chkBuoyVisible.set_sensitive( False )

        layoutBox_D_1 = gtk.HBox()
        lblKeyFrameCentreX = gtk.Label( "Centre X:" )
        layoutBox_D_1.pack_start( lblKeyFrameCentreX )
        lblKeyFrameCentreX.show()
        self.tbxKeyFrameCentreX = gtk.Entry()
        layoutBox_D_1.pack_start( self.tbxKeyFrameCentreX )
        self.tbxKeyFrameCentreX.connect( "focus-out-event", self.setKeyFrameDataFromControls )
        self.tbxKeyFrameCentreX.show()

        layoutBox_D_2 = gtk.HBox()
        lblKeyFrameCentreY = gtk.Label( "Centre Y:" )
        layoutBox_D_2.pack_start( lblKeyFrameCentreY )
        lblKeyFrameCentreY.show()
        self.tbxKeyFrameCentreY = gtk.Entry()
        layoutBox_D_2.pack_start( self.tbxKeyFrameCentreY )
        self.tbxKeyFrameCentreY.connect( "focus-out-event", self.setKeyFrameDataFromControls )
        self.tbxKeyFrameCentreY.show()

        layoutBox_D_3 = gtk.HBox()
        lblKeyFrameRadius = gtk.Label( "Radius:" )
        layoutBox_D_3.pack_start( lblKeyFrameRadius )
        lblKeyFrameRadius.show()
        self.tbxKeyFrameRadius = gtk.Entry()
        layoutBox_D_3.pack_start( self.tbxKeyFrameRadius )
        self.tbxKeyFrameRadius.connect( "focus-out-event", self.setKeyFrameDataFromControls )
        self.tbxKeyFrameRadius.show()

        layoutBox_C_1.pack_start( layoutBox_D_0, fill=False )
        layoutBox_D_0.show()
        layoutBox_C_1.pack_start( self.chkBuoyVisible )
        self.chkBuoyVisible.show()
        layoutBox_C_1.pack_start( layoutBox_D_1, fill=False )
        layoutBox_D_1.show()
        layoutBox_C_1.pack_start( layoutBox_D_2, fill=False )
        layoutBox_D_2.show()
        layoutBox_C_1.pack_start( layoutBox_D_3, fill=False )
        layoutBox_D_3.show()

        layoutBox_B_0.pack_start( layoutBox_C_0 )
        layoutBox_C_0.show()
        layoutBox_B_0.pack_start( layoutBox_C_1 )
        layoutBox_C_1.show()

        layoutBox_A_0.pack_start( layoutBox_B_0 )
        layoutBox_B_0.show()

        self.setCurFrameIdx( 0 )
    
        # Add the root layout box to the main window
        self.window.add( layoutBox_A_0 )
        layoutBox_A_0.show()
        
        # Finished so show the window
        self.window.show()

    #---------------------------------------------------------------------------
    def setCurFrameIdx( self, frameIdx ):

        if self.settingFrame:
            raise "NotReentrant"

        self.settingFrame = True

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
        self.curFramePixBuf = gtk.gdk.pixbuf_new_from_data( 
            pythonFrame.tostring(), 
            gtk.gdk.COLORSPACE_RGB,
            False,
            pythonFrame.depth,
            pythonFrame.width,
            pythonFrame.height,
            pythonFrame.width*pythonFrame.nChannels )

        # Update the text-box that displays the current frame number
        self.tbxFrameNumber.set_text( str( frameIdx + 1 ) )

        # Display the buoy position
        buoyData = self.groundTruthData.getBuoyData( frameIdx )
        
        self.chkBuoyVisible.set_active( buoyData.visible )
        self.tbxKeyFrameCentreX.set_text( str( buoyData.centreX ) )
        self.tbxKeyFrameCentreY.set_text( str( buoyData.centreY ) )
        self.tbxKeyFrameRadius.set_text( str( buoyData.radius ) )
        
        keyFrameType = self.groundTruthData.getKeyFrameType( frameIdx )
        
        for keyFrameTypeIdx in range( len( BuoyGroundTruth.KEYFRAME_TYPE_LIST ) ):
            if BuoyGroundTruth.KEYFRAME_TYPE_LIST[ keyFrameTypeIdx ] == keyFrameType:
                self.cbxKeyFrameType.set_active( keyFrameTypeIdx )
                break
        
        # Redraw the frame
        self.dwgCurFrame.queue_draw()
        
        self.settingFrame = False

    #---------------------------------------------------------------------------
    def setupControlsForKeyFrame( self, widget, data = None ):
        if self.cbxKeyFrameType.get_active_text() == BuoyGroundTruth.KEYFRAME_TYPE_VISIBLE:
            self.tbxKeyFrameCentreX.set_sensitive( True )
            self.tbxKeyFrameCentreY.set_sensitive( True )
            self.tbxKeyFrameRadius.set_sensitive( True )
        else:
            self.tbxKeyFrameCentreX.set_sensitive( False )
            self.tbxKeyFrameCentreY.set_sensitive( False )
            self.tbxKeyFrameRadius.set_sensitive( False )
        
        if not self.settingFrame:
            if self.cbxKeyFrameType.get_active_text() != BuoyGroundTruth.KEYFRAME_TYPE_VISIBLE:
                self.chkBuoyVisible.set_active( False )
                self.tbxKeyFrameCentreX.set_text( "0.0" )
                self.tbxKeyFrameCentreY.set_text( "0.0" )
                self.tbxKeyFrameRadius.set_text( "0.0" )
            self.setKeyFrameDataFromControls()
            
    #---------------------------------------------------------------------------
    def setKeyFrameDataFromControls( self, widget = None, data = None ):
 
        centreX = tryParseFloat( self.tbxKeyFrameCentreX.get_text(), 0.0 )
        centreY = tryParseFloat( self.tbxKeyFrameCentreY.get_text(), 0.0 )
        radius = tryParseFloat( self.tbxKeyFrameRadius.get_text(), 0.0 )

        keyFrame = KeyFrame( self.cbxKeyFrameType.get_active_text(), centreX, centreY, radius )
        
        if keyFrame.type == BuoyGroundTruth.KEYFRAME_TYPE_NONE:
            # Keyframes of type None don't need to be stored
            if self.curFrameIdx in self.keyFrames.keys():
                del  self.keyFrames[ self.curFrameIdx ]
        else:
            self.keyFrames[ self.curFrameIdx ] = keyFrame
            
        # Reset everything
        self.setCurFrameIdx( self.curFrameIdx )

    #---------------------------------------------------------------------------
    def gotoPrevFrame( self, widget, data = None ):
        self.setCurFrameIdx( self.curFrameIdx - 1 )

    #---------------------------------------------------------------------------
    def gotoNextFrame( self, widget, data = None ):
        self.setCurFrameIdx( self.curFrameIdx + 1 )
    
    #---------------------------------------------------------------------------
    def getImageRectangleInWidget( self, widget ):
        
        # Centre the image inside the widget
        widgetX, widgetY, widgetWidth, widgetHeight = widget.get_allocation()
        
        imgRect = gtk.gdk.Rectangle( 0, 0, widgetWidth, widgetHeight )
        
        if widgetWidth > self.frameWidth:
            imgRect.x = (widgetWidth - self.frameWidth) / 2
            imgRect.width = self.frameWidth
            
        if widgetHeight > self.frameHeight:
            imgRect.y = (widgetHeight - self.frameHeight) / 2
            imgRect.height = self.frameHeight
        
        return imgRect
    
    #---------------------------------------------------------------------------
    def onDwgCurFrameExpose( self, widget, event ):
    
        if self.curFramePixBuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                self.curFramePixBuf, srcX, srcY, 
                imgRect.x, imgRect.y, imgRect.width, imgRect.height )
                
            # Now draw the circle for the buoy on top
            buoyData = self.groundTruthData.getBuoyData( self.curFrameIdx )
            if buoyData.visible:
            
                arcX = int( imgOffsetX + buoyData.centreX - buoyData.radius )
                arcY = int( imgOffsetY + buoyData.centreY - buoyData.radius )
                arcWidth = arcHeight = int( buoyData.radius * 2 )
            
                drawFilledArc = False
                widget.window.draw_arc( widget.get_style().fg_gc[ gtk.STATE_NORMAL ], 
                    drawFilledArc, arcX, arcY, arcWidth, arcHeight, 0, 360 * 64 )
                
                widget.window.draw_points( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                    [ ( int( imgOffsetX + buoyData.centreX ), int( imgOffsetY + buoyData.centreY ) ) ] )
                

    #---------------------------------------------------------------------------
    def onDwgCurFrameButtonPress( self, widget, event ):
    
        buoyData = self.groundTruthData.getBuoyData( self.curFrameIdx )
        if buoyData.visible:
        
            imgRect = self.getImageRectangleInWidget( widget )
        
            self.tbxKeyFrameCentreX.set_text( str( event.x - imgRect.x ) )
            self.tbxKeyFrameCentreY.set_text( str( event.y - imgRect.y ) )
            self.setKeyFrameDataFromControls()

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
    def saveKeyFrameDataToFile( self, data ):
        self.setKeyFrameDataFromControls()  # Save any changes being made to the current keyframe
        self.groundTruthData.saveKeyFramesToFile( "keyframes.yaml" )
        
    #---------------------------------------------------------------------------
    def loadKeyFrameDataFromFile( self ):
        self.groundTruthData.loadKeyFramesFromFile( "keyframes.yaml" )
    
    #---------------------------------------------------------------------------
    def clearKeyFrames( self, data = None ):
        self.groundTruthData.clearKeyFrames()
        self.setCurFrameIdx( int( self.tbxFrameNumber.get_text() ) - 1 )

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.main()


