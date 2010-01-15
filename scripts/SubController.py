#! /usr/bin/python

#-------------------------------------------------------------------------------
# Control program for submarine
#-------------------------------------------------------------------------------

import cv
import pygtk
pygtk.require('2.0')
import gtk
import gobject

from playerc import *
import Profiling
#from ColourTracker import ColourTracker
from RoBoardControl import ColourTracker

ROBOT_TYPE_REAL = "Real"
ROBOT_TYPE_SIM = "Sim"



#-------------------------------------------------------------------------------
class MainWindow:

    #---------------------------------------------------------------------------
    def __init__( self ):

        self.robotType = ROBOT_TYPE_REAL
        self.curFramePixBuf = None
        self.processedFramePixBuf = None
        self.tracker = ColourTracker()
        
        self.frameWidth = 320
        self.frameHeight = 240
        
        # Create a client object
        self.playerClient = playerc_client( None, 'localhost', 6665 )
        # Connect it
        if self.playerClient.connect() != 0:
            raise playerc_error_str()

        self.playerPos3d = None
        if self.robotType == ROBOT_TYPE_SIM:
            # Create a proxy for position3d:0
            self.playerPos3d = playerc_position3d( self.playerClient, 0 )
            if self.playerPos3d.subscribe( PLAYERC_OPEN_MODE ) != 0:
                raise playerc_error_str()
        
        self.playerCamera = playerc_camera( self.playerClient, 0 )
        if self.playerCamera.subscribe( PLAYERC_OPEN_MODE ) != 0:
            raise playerc_error_str()

        if self.playerClient.datamode( PLAYERC_DATAMODE_PULL ) != 0:
            raise playerc_error_str()
    
        if self.playerClient.set_replace_rule( -1, -1, PLAYER_MSGTYPE_DATA, -1, 1 ) != 0:
            raise playerc_error_str()
    
        print "Connected to Player!"
        
        # Create a new window
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL)
    
        self.window.connect( "destroy", self.destroy )
    
        # Sets the border width of the window.
        self.window.set_border_width(10)

        # Layout box names have the format layoutBox_Level_Number
        layoutBox_A_0 = gtk.HBox()
        
        # Setup an drawing area to show the current frame
        self.dwgCurFrame = gtk.DrawingArea()
        self.dwgCurFrame.connect( "expose_event", self.onDwgCurFrameExpose )
        self.dwgCurFrame.set_size_request( self.frameWidth, self.frameHeight )
        layoutBox_A_0.pack_start( self.dwgCurFrame )
        self.dwgCurFrame.show()
        
        # Setup an drawing area to show the processed frame
        self.dwgProcessedFrame = gtk.DrawingArea()
        self.dwgProcessedFrame.connect( "expose_event", self.onProcessedCurFrameExpose )
        self.dwgProcessedFrame.set_size_request( self.frameWidth, self.frameHeight )
        layoutBox_A_0.pack_start( self.dwgProcessedFrame )
        self.dwgProcessedFrame.show()
        
        # Add the root layout box to the main window
        self.window.add( layoutBox_A_0 )
        layoutBox_A_0.show()
        
        asd = self.update()
        gobject.idle_add( asd.next )

        
        # Finished so show the window
        self.window.show()
    
    #---------------------------------------------------------------------------
    def destroy( self, widget, data = None ):
        # Shutdown
        #if None != self.videoCapture: 
        #    cv.ReleaseCapture( self.videoCapture )
        
        # Clean up
        self.playerCamera.unsubscribe()
        if self.playerPos3d != None:
            self.playerPos3d.unsubscribe()
        self.playerClient.disconnect()
        
        gtk.main_quit()
        
    #---------------------------------------------------------------------------   
    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()
        
    #---------------------------------------------------------------------------
    #@Profiling.printTiming
    def getImage( self ):
        self.playerClient.read()
        if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
            self.playerCamera.decompress()
            
        if self.playerCamera.compression != PLAYER_CAMERA_COMPRESS_RAW:
            print( "Error: Unable to decompress frame" );
            return None
       
        cvImage = cv.CreateImageHeader( ( self.playerCamera.width, self.playerCamera.height ), cv.IPL_DEPTH_8U, 3 )       
        cv.SetData( cvImage, self.playerCamera.image[:self.playerCamera.image_count], self.playerCamera.width*3 )

        #if self.robotType != ROBOT_TYPE_REAL:
        #    cv.CvtColor( cvImage, cvImage, cv.CV_RGB2BGR )
        
        return cvImage
        
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
                    
    #---------------------------------------------------------------------------
    def onProcessedCurFrameExpose( self, widget, event ):
    
        if self.processedFramePixBuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                self.processedFramePixBuf, srcX, srcY, 
                imgRect.x, imgRect.y, imgRect.width, imgRect.height )
                
            # Now draw the circle for the buoy on top
            blobData = self.tracker.getBlobData()
            if blobData.visible:
            
                arcX = int( imgOffsetX + blobData.centreX - blobData.radius )
                arcY = int( imgOffsetY + blobData.centreY - blobData.radius )
                arcWidth = arcHeight = int( blobData.radius * 2 )
            
                drawFilledArc = False
                graphicsContext = widget.window.new_gc()
                graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 65535, 65535 ) )
            
                widget.window.draw_arc( graphicsContext, 
                    drawFilledArc, arcX, arcY, arcWidth, arcHeight, 0, 360 * 64 )
                
                widget.window.draw_points( graphicsContext,
                    [ ( int( imgOffsetX + blobData.centreX ), int( imgOffsetY + blobData.centreY ) ) ] )
    
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
      
    def update( self ):
    
        while 1:
            if self.playerClient.peek( 0 ):
                self.getAndProcessFrame()
                     
            blobData = self.tracker.getBlobData()
            #if blobData.visible:
            #    print "Buoy Visible at ( " + str( blobData.centreX ) + ", " + str( blobData.centreY ) + " )"
            #else:
            #    print "Can't see blob"
                
            yield True
            
        yield False

    @Profiling.printTiming
    def getAndProcessFrame( self ):
        frame = self.getImage()
                
        #cv.CvtColor( frame, frame, cv.CV_RGB2BGR )
        processedFrameData = self.tracker.processFrame( frame )
        
        #processedFrame = cv.CreateImageHeader( ( self.playerCamera.width, self.playerCamera.height ), cv.IPL_DEPTH_8U, 3 )       
        #cv.SetData( cvImage, processedFrameData, self.playerCamera.width*3 )

        
        #cv.CvtColor( processedFrame, processedFrame, cv.CV_BGR2RGB )
        self.curFramePixBuf = gtk.gdk.pixbuf_new_from_data( 
            frame.tostring(), 
            gtk.gdk.COLORSPACE_RGB,
            False,
            frame.depth,
            frame.width,
            frame.height,
            frame.width*frame.nChannels )
            
        self.processedFramePixBuf = gtk.gdk.pixbuf_new_from_data( 
            processedFrameData, 
            gtk.gdk.COLORSPACE_RGB,
            False,
            frame.depth,
            frame.width,
            frame.height,
            frame.width*frame.nChannels )
            
        # Redraw the frames
        self.dwgCurFrame.queue_draw()
        self.dwgProcessedFrame.queue_draw()



    








                
    #print frameNum



#-------------------------------------------------------------------------------
if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.main()


    
