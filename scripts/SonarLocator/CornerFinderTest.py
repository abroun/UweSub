#! /usr/bin/python

import sys
import math
import os.path

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import cv

#from CornerFinder import findCorner as CF_FindCorner
from RoBoardControl import findCorner as CF_FindCorner

#-------------------------------------------------------------------------------
class MainWindow:

    #TEST_IMAGE_NAME = "../../data/SonarTest/black_sonar_90m.png"
    TEST_IMAGE_NAME = "../../data/SonarTest/black_sonar_pool.png"
    #TEST_IMAGE_NAME = "../../data/SonarTest/corner.png"
 
    #---------------------------------------------------------------------------
    def __init__( self ):
    
        self.curFrameIdx = -1
        self.rawImagePixBuf = None
        self.processedImagePixBuf = None
        self.lines = None
        self.corner = None
        
        # Setup the GUI
        builder = gtk.Builder()
        builder.add_from_file( "CornerFinderTest.glade" )
        
        self.window = builder.get_object( "winMain" )
        self.dwgRaw = builder.get_object( "dwgRaw" )
        self.dwgProcessed = builder.get_object( "dwgProcessed" )
        
        builder.connect_signals( self )
        
        self.rawImage = cv.LoadImage( self.TEST_IMAGE_NAME )    
        self.processRawImage()
        
        self.window.show()
        
        updateLoop = self.update()
        gobject.idle_add( updateLoop.next )
        
    #---------------------------------------------------------------------------
    def onWinMainDestroy( self, widget, data = None ):  
        gtk.main_quit()
        
    #---------------------------------------------------------------------------   
    def main( self ):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()
        
    #---------------------------------------------------------------------------
    def onDwgRawExposeEvent( self, widget, event ):
    
        if self.rawImagePixBuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget,
                self.rawImagePixBuf.get_width(), self.rawImagePixBuf.get_height() )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                self.rawImagePixBuf, srcX, srcY, 
                imgRect.x, imgRect.y, imgRect.width, imgRect.height )

    #---------------------------------------------------------------------------
    def onDwgProcessedExposeEvent( self, widget, event ):
    
        if self.processedImagePixBuf != None:
            
            imgRect = self.getImageRectangleInWidget( widget,
                self.processedImagePixBuf.get_width(), self.processedImagePixBuf.get_height() )
                
            imgOffsetX = imgRect.x
            imgOffsetY = imgRect.y
                
            # Get the total area that needs to be redrawn
            imgRect = imgRect.intersect( event.area )
        
            srcX = imgRect.x - imgOffsetX
            srcY = imgRect.y - imgOffsetY
           
            widget.window.draw_pixbuf( widget.get_style().fg_gc[ gtk.STATE_NORMAL ],
                self.processedImagePixBuf, srcX, srcY, 
                imgRect.x, imgRect.y, imgRect.width, imgRect.height )
                
            # Now draw the features
            graphicsContext = widget.window.new_gc()
            self.drawLines( imgRect, widget.window, graphicsContext, self.lines )
            #drawFilledArc = True
            #graphicsContext = widget.window.new_gc()
            
            if self.corner != None:
                
                arcX = int( imgRect.x + self.corner[ 0 ] - 5 )
                arcY = int( imgRect.y + self.corner[ 1 ] - 5 )
                arcWidth = arcHeight = 10
            
                drawFilledArc = True
                graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 65535, 0 ) )

                widget.window.draw_arc( graphicsContext, 
                    drawFilledArc, arcX, arcY, arcWidth, arcHeight, 0, 360 * 64 )


            #for featureIdx in range( len( self.features ) ):
                
                #feature = self.features[ featureIdx ]
                
                #if featureIdx in self.trackedFeatureMatchIdxList:
                    #self.drawSurfFeature( imgRect, widget.window, graphicsContext, feature )
                #else:
                    #graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 65535, 0 ) )
                
                    #arcX = imgRect.x + feature.x - 2
                    #arcY = imgRect.y + feature.y - 2
                    
                    #widget.window.draw_arc( graphicsContext, 
                        #drawFilledArc, int( arcX ), int( arcY ), 4, 4, 0, 360 * 64 )
                    
            ## Draw the best fit line if possible
            #if self.bestFitLine != None:
                #graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 0, 0, 65535 ) )
                #self.drawLine( imgRect, widget.window, graphicsContext, self.bestFitLine )
                
            #if self.bestFitLineGA != None:
                #graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 65535, 0 ) )
                #self.drawLine( imgRect, widget.window, graphicsContext, self.bestFitLineGA )
            
            #if self.manualLine != None:
                #graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 0, 0 ) )
                #self.drawLine( imgRect, widget.window, graphicsContext, self.manualLine )
     
    #---------------------------------------------------------------------------
    def drawLines( self, imgRect, drawable, graphicsContext, lines ):
        
        graphicsContext.set_rgb_fg_color( gtk.gdk.Color( 65535, 0, 0 ) )
        
        #lines = [(100.0, 45.0*math.pi/180.0)]
        
        if lines != None:
            
            for line in lines:
                
                print line
                
                distance = line[ 0 ]
                theta = line[ 1 ]
                
                centreX = distance*math.cos( theta )
                centreY = distance*math.sin( theta )
                dirX = math.sin( theta )
                dirY = -math.cos( theta )
                
                x1 = int( centreX - 2000*dirX )
                y1 = int( centreY - 2000*dirY )
                x2 = int( centreX + 2000*dirX )
                y2 = int( centreY + 2000*dirY )
        
                drawable.draw_line( graphicsContext, x1, y1, x2, y2 )            
    
    #---------------------------------------------------------------------------
    def getImageRectangleInWidget( self, widget, imageWidth, imageHeight ):
        
        # Centre the image inside the widget
        widgetX, widgetY, widgetWidth, widgetHeight = widget.get_allocation()
        
        imgRect = gtk.gdk.Rectangle( 0, 0, widgetWidth, widgetHeight )
        
        if widgetWidth > imageWidth:
            imgRect.x = (widgetWidth - imageWidth) / 2
            imgRect.width = imageWidth
            
        if widgetHeight > imageHeight:
            imgRect.y = (widgetHeight - imageHeight) / 2
            imgRect.height = imageHeight
        
        return imgRect
       
    #---------------------------------------------------------------------------
    def update( self ):
    
        while 1:
        
            yield True
            
        yield False
            
    #---------------------------------------------------------------------------
    def processRawImage( self ):
        
        # Resize the image if needed
        #requiredScaleX = 1.0
        #if self.rawImage.width > self.MAX_IMAGE_WIDTH:
            #requiredScaleX = float( self.MAX_IMAGE_WIDTH ) / float( self.rawImage.width )
        #requiredScaleY = 1.0
        #if self.rawImage.height > self.MAX_IMAGE_HEIGHT:
            #requiredScaleY = float( self.MAX_IMAGE_HEIGHT ) / float( self.rawImage.height )
            
        #requiredScale = requiredScaleX
        #if requiredScaleY < requiredScaleX:
            #requiredScale = requiredScaleY
        
        #if requiredScale < 1.0:
            #scaledImage = cv.CreateImage( 
                #( self.rawImage.width*requiredScale, self.rawImage.height*requiredScale ), 
                #self.rawImage.depth, self.rawImage.nChannels )
                
            #cv.Resize( self.rawImage, scaledImage )
            #self.rawImage = scaledImage
        
        # Convert the image to grayscale
        rawImageSize = ( self.rawImage.width, self.rawImage.height )
        self.rawImageGray = cv.CreateImage( rawImageSize, cv.IPL_DEPTH_8U, 1 )
        cv.CvtColor( self.rawImage, self.rawImageGray, cv.CV_RGB2GRAY )
        
        # Process the image
        self.lines, thresholdedImage, self.corner = CF_FindCorner( self.rawImageGray )
        temp = cv.CreateImageHeader( ( self.rawImage.width, self.rawImage.height ), cv.IPL_DEPTH_8U, 1 )       
        cv.SetData( temp, thresholdedImage, self.rawImage.width )
        thresholdedImage = temp
            
        rgbThresholdedImage = cv.CreateImage( ( thresholdedImage.width, thresholdedImage.height ), cv.IPL_DEPTH_8U, 3 )
        cv.CvtColor( thresholdedImage, rgbThresholdedImage, cv.CV_GRAY2RGB )

        #processedImage = self.rawImage
        processedImage = rgbThresholdedImage
        
        # Create a pixbuf to display the raw image    
        self.rawImagePixBuf = gtk.gdk.pixbuf_new_from_data( 
            self.rawImage.tostring(), 
            gtk.gdk.COLORSPACE_RGB,
            False,
            self.rawImage.depth,
            self.rawImage.width,
            self.rawImage.height,
            self.rawImage.width*self.rawImage.nChannels )
            
        # Do the same for the processed image
        self.processedImagePixBuf = gtk.gdk.pixbuf_new_from_data( 
            processedImage.tostring(), 
            gtk.gdk.COLORSPACE_RGB,
            False,
            processedImage.depth,
            processedImage.width,
            processedImage.height,
            processedImage.width*processedImage.nChannels )
        
        # Resize the drawing areas if necessary
        if self.dwgRaw.get_size_request() != ( self.rawImage.width, self.rawImage.height ):
            self.dwgRaw.set_size_request( self.rawImage.width, self.rawImage.height )
        if self.dwgProcessed.get_size_request() != ( processedImage.width, processedImage.height ):
            self.dwgProcessed.set_size_request( processedImage.width, processedImage.height )

        # Update the display
        self.dwgRaw.queue_draw()
        self.dwgProcessed.queue_draw()
        
#-------------------------------------------------------------------------------
if __name__ == "__main__":

    mainWindow = MainWindow()
    mainWindow.main()
