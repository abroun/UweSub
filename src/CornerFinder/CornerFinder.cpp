//------------------------------------------------------------------------------
// File: CornerFinder.cpp
// Desc: Provides routines for finding a corner in a sonar image
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include "CornerFinder.h"

#include <cv.h>
#include <cvaux.h>
#include <highgui.h>

//------------------------------------------------------------------------------
void CF_FindCorner( const _IplImage* pImage, _IplImage** ppProcessedImageOut )
{
    IplImage* pProcessedImage = cvCloneImage( pImage );
    
    
    if ( NULL != ppProcessedImageOut )
    {
        *ppProcessedImageOut = pProcessedImage;
    }
}
