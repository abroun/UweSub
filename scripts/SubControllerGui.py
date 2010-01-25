#! /usr/bin/python
#-------------------------------------------------------------------------------
# GUI for submarine control program
#-------------------------------------------------------------------------------

import cv
import pygtk
pygtk.require('2.0')
import gtk
import gobject
from SubController import SubController

#-------------------------------------------------------------------------------
class MainWindow:

    #---------------------------------------------------------------------------
    def __init__( self ):

        self.subController = SubController()
        self.curFramePixBuf = None
        self.processedFramePixBuf = None
        
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
        self.dwgCurFrame.set_size_request( self.subController.frameWidth, self.subController.frameHeight )
        layoutBox_A_0.pack_start( self.dwgCurFrame )
        self.dwgCurFrame.show()
        
        # Setup an drawing area to show the processed frame
        self.dwgProcessedFrame = gtk.DrawingArea()
        self.dwgProcessedFrame.connect( "expose_event", self.onProcessedCurFrameExpose )
        self.dwgProcessedFrame.set_size_request( self.subController.frameWidth, self.subController.frameHeight )
        layoutBox_A_0.pack_start( self.dwgProcessedFrame )
        self.dwgProcessedFrame.show()
        
        # Add the root layout box to the main window
        self.window.add( layoutBox_A_0 )
        layoutBox_A_0.show()
        
        updateLoop = self.update()
        gobject.idle_add( updateLoop.next )

        # Finished so show the window
        self.window.show()
    
    #---------------------------------------------------------------------------
    def destroy( self, widget, data = None ):
        
        # Clean up
        self.subController.shutdown()
        
        gtk.main_quit()
        
    #---------------------------------------------------------------------------   
    def main( self ):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()
        
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
            blobData = self.subController.tracker.getBlobData()
            if blobData.visible:
            
                arcX = int( imgOffsetX + blobData.centreX - blobData.radius )
                arcY = int( imgOffsetY + blobData.centreY - blobData.radius )
                arcWidth = arcHeight = int( blobData.radius * 2 )
            
                drawFilledArc = False
                graphicsContext = widget.window.new_gc()
                graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 65535, 0 ) )
            
                widget.window.draw_arc( graphicsContext, 
                    drawFilledArc, arcX, arcY, arcWidth, arcHeight, 0, 360 * 64 )
                
                widget.window.draw_points( graphicsContext,
                    [ ( int( imgOffsetX + blobData.centreX ), int( imgOffsetY + blobData.centreY ) ) ] )
    
    #---------------------------------------------------------------------------
    def getImageRectangleInWidget( self, widget ):
        
        # Centre the image inside the widget
        widgetX, widgetY, widgetWidth, widgetHeight = widget.get_allocation()
        
        imgRect = gtk.gdk.Rectangle( 0, 0, widgetWidth, widgetHeight )
        
        if widgetWidth > self.subController.frameWidth:
            imgRect.x = (widgetWidth - self.subController.frameWidth) / 2
            imgRect.width = self.subController.frameWidth
            
        if widgetHeight > self.subController.frameHeight:
            imgRect.y = (widgetHeight - self.subController.frameHeight) / 2
            imgRect.height = self.subController.frameHeight
        
        return imgRect
      
    #---------------------------------------------------------------------------
    def update( self ):
    
        while 1:
            newFrameAvailable = self.subController.update()
            if newFrameAvailable:
                
                frame = self.subController.frame
                processedFrameData = self.subController.processedFrameData
                
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
                
            yield True
            
        yield False

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    mainWindow = MainWindow()
    mainWindow.main()