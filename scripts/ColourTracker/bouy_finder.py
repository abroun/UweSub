#!/usr/bin/env python

import cv

class BouyFinder:

    def __init__(self):
        self.capture = cv.CaptureFromCAM(0)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, 120)    # massively drop image size for roboard ( less processing)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 180)   # again
        #cv.NamedWindow( "CamShiftDemo", 1 )
        #cv.NamedWindow( "GreyTimes" , 1)    # create a window for displaying the image
        #cv.NamedWindow( "FunkyThresh", 1)   # create a window for displaying the image
        #cv.NamedWindow( "LoadedImage", 1)   # create a window for displaying the image
        #cv.NamedWindow( "HueSmooth", 1)
    
        self.pixel_count = 0
        self.target_aquired = 0
        self.central_x = 0
        self.central_y = 0
        self.corr_x = 0
        self.corr_y = 0

    def run(self):
        backproject_mode = False
        frame = cv.QueryFrame( self.capture ) # sets up capture
        loadimg = cv.CreateImage(cv.GetSize(frame), frame.depth, 1)     # creates a memory space for static image
        #loadimg = cv.LoadImage("underwater_3.png")            # loads image file
        while True:
            frame = cv.QueryFrame( self.capture ) # capture camera image
            loadimg = frame
            grey_tmp = cv.CreateImage(cv.GetSize(loadimg), loadimg.depth, 3)    # temp data storage
            threshtimes = cv.CreateImage(cv.GetSize(loadimg), loadimg.depth, 1) # thresh data storage
            cv.CvtColor(loadimg,grey_tmp, cv.CV_BGR2HSV)            # convert from colour to grey
            hue = cv.CreateImage(cv.GetSize(loadimg), loadimg.depth, 1)
            hue_smooth = cv.CreateImage(cv.GetSize(loadimg), loadimg.depth, 1)
            cv.Split(grey_tmp, hue, None, None, None)
            cv.Smooth(hue,hue_smooth,cv.CV_MEDIAN,5,0,0,0)
            cv.Threshold(hue,threshtimes,10,255,cv.CV_THRESH_BINARY)    # do the thresholding (150 seems good for underwater orange)
            #cv.AdaptiveThreshold(hue_smooth,threshtimes, 255, cv.CV_ADAPTIVE_THRESH_MEAN_C, cv.CV_THRESH_BINARY, 7, 15) #seems to be good for edge detection etc
            x_val = 0
            y_val = 0
            self.pixel_count = 0
        
            for x in range (threshtimes.height):    # for x
                for y in range (threshtimes.width):     # for y
                    pixel = threshtimes[ x , y]     # grabs the pixel data at (x,y)
                    if pixel == 0:          # if black is found 
                        x_val += x          # increment x counter
                        y_val += y          # increment y counter
                        self.pixel_count += 1       # increment pixel counter
             
            if self.pixel_count >= 100: # divide by 0 protection / noise removal
                self.target_aquired = 1  # awesome times detected
                self.central_x = y_val / self.pixel_count # calculates the x centre position
                self.central_y = x_val / self.pixel_count # calculates the y centre position
                x_draw1 = self.central_x + 100
                x_draw2 = self.central_x - 100
                y_draw1 = self.central_y + 100
                y_draw2 = self.central_y - 100
            
                cv.Line(loadimg,(x_draw1,self.central_y),(x_draw2,self.central_y),cv.CV_RGB(255,0,0),1,8,0)
                cv.Line(loadimg,(self.central_x,y_draw1),(self.central_x,y_draw2),cv.CV_RGB(255,0,0),1,8,0)
        
            else: # no bouy found
                self.target_aquired = 0  # bad times ahead
                self.corr_x = 0
                self.corr_y = 0
                self.pixel_count = 0
            
            self.corr_x = self.central_x - (threshtimes.width/2)
            self.corr_y = (threshtimes.height/2) - self.central_y
        
            #print "center x =" ,self.corr_x, "y =", self.corr_y, "area =", self.pixel_count # prints the returned values
            
            #cv.ShowImage( "GreyTimes", grey_tmp)    # display the grey scale
            #cv.ShowImage( "FunkyThresh", threshtimes)   # display the threshold image
            #cv.ShowImage( "LoadedImage", loadimg)   # display original image
            #cv.ShowImage( "HueSmooth", hue_smooth)
            #cv.ReleaseCapture(loadimg)
            c = cv.WaitKey(7)
            if c == 27:
                break
            elif c == ord("b"):
                backproject_mode = not backproject_mode

if __name__=="__main__":
    demo = BouyFinder()
    demo.run()