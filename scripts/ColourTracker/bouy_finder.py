#!/usr/bin/env python

import cv

class BouyFinder:

    def __init__(self):
        self.capture = cv.CaptureFromCAM(0)
	cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, 120) 	# massively drop image size for roboard ( less processing)
	cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 180)   # again
        #cv.NamedWindow( "CamShiftDemo", 1 )
	#cv.NamedWindow( "GreyTimes" , 1) 	# create a window for displaying the image
	#cv.NamedWindow( "FunkyThresh", 1)	# create a window for displaying the image
	#cv.NamedWindow( "LoadedImage", 1) 	# create a window for displaying the image
	
	self.pixel_count = 0
	self.target_aquired = 0

    def foundBouy():
	if self.pixel_count >= 20: # if area > 20 then we have found a bouy
	  self.target_aquired = 1  # awesome times detected
	else:
	  self.target_aquired = 0  # bad times ahead

    def run(self):
        backproject_mode = False
	frame = cv.QueryFrame( self.capture ) # sets up capture
	loadimg = cv.CreateImage(cv.GetSize(frame), frame.depth, 1) 	# creates a memory space for static image
	#loadimg = cv.LoadImage("underwater.png")			# loads image file
        
	frame = cv.QueryFrame( self.capture ) # capture camera image
	loadimg = frame
	canny_tmp = cv.CreateImage(cv.GetSize(loadimg), loadimg.depth, 1) 	# temp data storage
	threshtimes = cv.CreateImage(cv.GetSize(loadimg), loadimg.depth, 1) # thresh data storage
	cv.CvtColor(loadimg,canny_tmp,cv.CV_RGB2GRAY)			# convert from colour to grey
	cv.Threshold(canny_tmp,threshtimes,150,255,cv.CV_THRESH_BINARY)	# do the thresholding (150 seems good for underwater orange)

	x_val = 0
	y_val = 0
	self.pixel_count = 0
	    
	for x in range (threshtimes.height): 	# for x
	  for y in range (threshtimes.width): 	# for y
	    pixel = threshtimes[ x , y] 	# grabs the pixel data at (x,y)
	    if pixel == 0:			# if black is found 
	      x_val += x			# increment x counter
	      y_val += y			# increment y counter
	      self.pixel_count += 1		# increment pixel counter
		     
	if self.pixel_count != 0: # divide by 0 protection
	   central_x = y_val / self.pixel_count # calculates the x centre position
	   central_y = x_val / self.pixel_count # calculates the y centre position
	    
	else: # no bouy found
	   central_x = 0
	   central_y = 0
	    
	#print "center x =" ,central_x, "y =", central_y, "area =", self.pixel_count # prints the returned values
	#cv.ShowImage( "GreyTimes", canny_tmp)	# display the grey scale
	#cv.ShowImage( "FunkyThresh", threshtimes)	# display the threshold image
	#cv.ShowImage( "LoadedImage", loadimg)	# display original image
        c = cv.WaitKey(7)
        if c == 27:
            break
        elif c == ord("b"):
            backproject_mode = not backproject_mode

if __name__=="__main__":
    demo = BouyFinder()
    demo.run()
