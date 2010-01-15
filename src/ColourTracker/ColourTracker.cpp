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
const float ColourTracker::DEFAULT_TRACKED_HUE = (15.0f / 360.0f)*180.0f;
const float ColourTracker::DEFAULT_MAX_ABS_HUE_DIFF = (5.0f / 360.0f)*180.0f;
const bool ColourTracker::DEFAULT_CALCULATE_RADIUS = true;

//------------------------------------------------------------------------------
ColourTracker::ColourTracker( float trackedHue, float maxAbsHueDiff, bool bCalculateRadius )
{
    Reset();
    mTrackedHue = trackedHue;
    mMaxAbsHueDiff = maxAbsHueDiff;
    mbCalculateRadius = bCalculateRadius;
}

//------------------------------------------------------------------------------
void ColourTracker::Reset()
{
    mBlobData = BlobData( false, 0.0f, 0.0f, 0.0f );
}

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
    IplImage* pProcessedFrame = cvCreateImage( cvSize( pFrame->width, pFrame->height ), pFrame->depth, pFrame->nChannels );
    IplImage* pHSVFrame = cvCreateImage( cvSize( pFrame->width, pFrame->height ), pFrame->depth, pFrame->nChannels );
    cvCvtColor( pFrame, pHSVFrame, CV_RGB2HSV );
    pProcessedFrame = cvCloneImage( pFrame );
        
    // Loop through each pixel in the frame looking for orange pixels
    int centreX = 0;
    int centreY = 0;
    int numMatchingPixels = 0;
    COORD matchingPixelList[ 320*240 ];

    //int testHue = (int)mTrackedHue;
    //int maxAbsHueDiff = (int)mMaxAbsHueDiff;
      
    for ( int y = 0; y < pHSVFrame->height; y++ )
    {
        unsigned char* pCurPixel = (unsigned char*)&pHSVFrame->imageData[ y*pHSVFrame->width*pHSVFrame->nChannels ];
        for ( int x = 0; x < pHSVFrame->width; x++ )
        {
            const float DEFAULT_TRACKED_SATURATION = (91.0f / 100.0f)*255.0f;
            const float DEFAULT_TRACKED_VALUE = (91.0f / 100.0f)*255.0f;
            
            float pixelHue = (float)pCurPixel[ 0 ];
            float pixelSaturation = (float)pCurPixel[ 2 ];
            float pixelValue = (float)pCurPixel[ 2 ];
            
            // Determine the difference from the target hue in the range [-90..90)
            float hueDiff = mTrackedHue - pixelHue;
            while ( hueDiff < -90.0f )
            {
                hueDiff += 18.0f;
            }
            while ( hueDiff >= 90.0f )
            {
                hueDiff -= 180.0f;
            }

            // Check to see if the hue difference is small enough
            if ( hueDiff >= -mMaxAbsHueDiff 
                && hueDiff <= mMaxAbsHueDiff 
                && fabsf( pixelSaturation - DEFAULT_TRACKED_SATURATION ) < 5.0f
                && fabsf( pixelValue - DEFAULT_TRACKED_VALUE ) < 5.0f )
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
                
    // Return the centre of mass of all the 'orangish' pixels
    printf( "Num Matching Pixels = %i\n", numMatchingPixels );
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
    
    cvReleaseImage( &pHSVFrame );
    return pProcessedFrame;
}


