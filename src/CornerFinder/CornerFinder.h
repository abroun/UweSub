//------------------------------------------------------------------------------
// File: CornerFinder.h
// Desc: Provides routines for finding a corner in a sonar image
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef CORNER_FINDER_H
#define CORNER_FINDER_H

//------------------------------------------------------------------------------
struct _IplImage;

//------------------------------------------------------------------------------
void CF_FindCorner( const _IplImage* pImage, _IplImage** ppProcessedImageOut );

#endif // CORNER_FINDER_H
