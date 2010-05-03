//------------------------------------------------------------------------------
// File: ColourTracker.cpp
// Desc: Tracks a coloured blob by looking for the centre of mass of 
//       appropriately coloured pixels
//------------------------------------------------------------------------------
#include "ColourTracker.h"

#include <cv.h>
#include <cvaux.h>
#include <highgui.h>

#define CT_MAX( a, b ) ( a > b ? a : b )
#define CT_MIN( a, b ) ( a < b ? a : b )

//------------------------------------------------------------------------------
// BlobData
//------------------------------------------------------------------------------
BlobData::BlobData( bool bVisible, float centreX, float centreY, float radius )
{
    mbVisible = bVisible;
    mCentreX = centreX;
    mCentreY = centreY;
    mRadius = radius;
}

//------------------------------------------------------------------------------
// ColourTracker
//------------------------------------------------------------------------------
const float ColourTracker::MAX_HUE = 360.0f;
const float ColourTracker::MAX_SATURATION = 100.0f;
const float ColourTracker::MAX_VALUE = 100.0f;
const float ColourTracker::OPENCV_MAX_HUE = 180.0f;
const float ColourTracker::OPENCV_MAX_SATURATION = 255.0f;
const float ColourTracker::OPENCV_MAX_VALUE = 255.0f;

const float ColourTracker::DEFAULT_TRACKED_HUE = (15.0f / MAX_HUE)*OPENCV_MAX_HUE;
const float ColourTracker::DEFAULT_MAX_ABS_HUE_DIFF = (5.0f / MAX_HUE)*OPENCV_MAX_HUE;
const float ColourTracker::DEFAULT_TRACKED_SATURATION = -1.0f;
const float ColourTracker::DEFAULT_MAX_ABS_SATURATION_DIFF = (2.5f/MAX_SATURATION)*OPENCV_MAX_SATURATION;
const float ColourTracker::DEFAULT_TRACKED_VALUE = -1.0f;
const float ColourTracker::DEFAULT_MAX_ABS_VALUE_DIFF = (2.5f/MAX_VALUE)*OPENCV_MAX_VALUE;

const bool ColourTracker::DEFAULT_CALCULATE_RADIUS = true;

//------------------------------------------------------------------------------
ColourTracker::ColourTracker( float trackedHue, float maxAbsHueDiff, bool bCalculateRadius )
{
    Reset();
    mTrackedHue = trackedHue;
    mMaxAbsHueDiff = maxAbsHueDiff;
    mTrackedSaturation = DEFAULT_TRACKED_SATURATION;
    mMaxAbsSaturationDiff = DEFAULT_MAX_ABS_SATURATION_DIFF;
    mTrackedValue = DEFAULT_TRACKED_VALUE;
    mMaxAbsValueDiff = DEFAULT_MAX_ABS_VALUE_DIFF;
    
    mbCalculateRadius = bCalculateRadius;
}

//------------------------------------------------------------------------------
void ColourTracker::Reset()
{
    mBlobData = BlobData( false, 0.0f, 0.0f, 0.0f );
}

//------------------------------------------------------------------------------
typedef struct
{
    int x;
    int y;
} COORD;

//------------------------------------------------------------------------------
IplImage* ColourTracker::ProcessFrame( const IplImage* pFrame )
{
    // This routine expects BGR frames...
        
    // Convert the frame to HSV
    IplImage* pProcessedFrame = cvCloneImage( pFrame );
    IplImage* pHSVFrame = cvCreateImage( cvSize( pFrame->width, pFrame->height ), pFrame->depth, pFrame->nChannels );
    cvCvtColor( pFrame, pHSVFrame, CV_RGB2HSV );
    
    // Loop through each pixel in the frame looking for pixels that are close enough to the tracked colour
    int centreX = 0;
    int centreY = 0;
    int numMatchingPixels = 0;
    COORD* matchingPixelList = new COORD[ pFrame->width*pFrame->height ];
    
    bool bHueTracked = mTrackedHue >= 0.0f;
    bool bSaturationTracked = mTrackedSaturation >= 0.0f;
    bool bValueTracked = mTrackedValue >= 0.0f;
    
    // Check that there is a colour to track
    if ( bHueTracked || bSaturationTracked || bValueTracked )
    {
        // If there is then check each pixel against it
        for ( int y = 0; y < pHSVFrame->height; y++ )
        {
            unsigned char* pCurPixel = (unsigned char*)&pHSVFrame->imageData[ y*pHSVFrame->width*pHSVFrame->nChannels ];
            for ( int x = 0; x < pHSVFrame->width; x++ )
            {                
                float pixelHue = (float)pCurPixel[ 0 ];
                float pixelSaturation = (float)pCurPixel[ 1 ];
                float pixelValue = (float)pCurPixel[ 2 ];
                
                // Determine the difference from the target hue in the range [-90..90)
                float hueDiff = mTrackedHue - pixelHue;
                while ( hueDiff < -90.0f )
                {
                    hueDiff += 180.0f;
                }
                while ( hueDiff >= 90.0f )
                {
                    hueDiff -= 180.0f;
                }

                // Check to see if the colour difference is small enough
                bool bHueOk = !bHueTracked || ( hueDiff >= -mMaxAbsHueDiff && hueDiff <= mMaxAbsHueDiff );
                bool bSaturationOk = !bSaturationTracked || fabsf( pixelSaturation - mTrackedSaturation ) < mMaxAbsSaturationDiff;
                bool bValueOk = !bValueTracked || fabsf( pixelValue - mTrackedValue ) < mMaxAbsValueDiff;
                
                if ( bHueOk && bSaturationOk && bValueOk )
                {
                    centreX += x;
                    centreY += y;

                    if ( mbCalculateRadius )
                    {
                        matchingPixelList[ numMatchingPixels ].x = x;
                        matchingPixelList[ numMatchingPixels ].y = y;
                    }

                    numMatchingPixels++;
                    
                    unsigned char* pPixelToModify = (unsigned char*)&pProcessedFrame->imageData[ y*pProcessedFrame->width*pProcessedFrame->nChannels + x*pProcessedFrame->nChannels ];
                    pPixelToModify[ 0 ] = 255;
                    pPixelToModify[ 1 ] = 255;
                    pPixelToModify[ 2 ] = 255;     
                }
                       
                // Move onto the next pixel
                pCurPixel += pHSVFrame->nChannels;
            }
        }
    }
                
    // Return the centre of mass of all the matching pixels
    //printf( "Num Matching Pixels = %i\n", numMatchingPixels );
    if ( numMatchingPixels > 0 )
    {
        centreX /= numMatchingPixels;
        centreY /= numMatchingPixels;
        mBlobData = BlobData( true, centreX, centreY, 10.0f );
        
        // Set the radius as the standard deviation of the blob
        if ( mbCalculateRadius )
        {
            int squaredDistanceSum = 0;
            for ( int pixelIdx = 0; pixelIdx < numMatchingPixels; pixelIdx++ )
            {
                int xDiff = matchingPixelList[ pixelIdx ].x - centreX;
                int yDiff = matchingPixelList[ pixelIdx ].y - centreY;

                squaredDistanceSum += (xDiff*xDiff + yDiff*yDiff);
            }
            
            int variance = squaredDistanceSum / numMatchingPixels;
            mBlobData.mRadius = sqrt( variance );
        }
    }
    else
    {
        mBlobData.mbVisible = false;
    }
    
    delete [] matchingPixelList;
    cvReleaseImage( &pHSVFrame );
    return pProcessedFrame;
}

//------------------------------------------------------------------------------
void ColourTracker::SetTrackedHue( float trackedHue, float maxAbsHueDiff )
{
    mTrackedHue = trackedHue;
    if ( mTrackedHue >= 0.0f )
    {
        if ( mTrackedHue > MAX_HUE )
        {
            mTrackedHue = MAX_HUE;
        }
        mTrackedHue = (mTrackedHue/MAX_HUE)*OPENCV_MAX_HUE;
        mMaxAbsHueDiff = (maxAbsHueDiff/MAX_HUE)*OPENCV_MAX_HUE;
    }
}

//------------------------------------------------------------------------------
void ColourTracker::SetTrackedSaturation( float trackedSaturation, float maxAbsSaturationDiff )
{
    mTrackedSaturation = trackedSaturation;
    if ( mTrackedSaturation >= 0.0f )
    {
        if ( mTrackedSaturation > MAX_SATURATION )
        {
            mTrackedSaturation = MAX_SATURATION;
        }
        mTrackedSaturation = (mTrackedSaturation/MAX_SATURATION)*OPENCV_MAX_SATURATION;
        mMaxAbsSaturationDiff = (maxAbsSaturationDiff/MAX_SATURATION)*OPENCV_MAX_SATURATION;
    }
}

//------------------------------------------------------------------------------
void ColourTracker::SetTrackedValue( float trackedValue, float maxAbsValueDiff )
{
    mTrackedValue = trackedValue;
    if ( mTrackedValue >= 0.0f )
    {
        if ( mTrackedValue > MAX_VALUE )
        {
            mTrackedValue = MAX_VALUE;
        }
        mTrackedValue = (mTrackedValue/MAX_VALUE)*OPENCV_MAX_VALUE;
        mMaxAbsValueDiff = (maxAbsValueDiff/MAX_VALUE)*OPENCV_MAX_VALUE;
    }
}



