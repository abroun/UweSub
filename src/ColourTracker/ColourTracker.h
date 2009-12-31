//------------------------------------------------------------------------------
// File: ColourTracker.h
// Desc: Tracks a coloured blob by looking for the centre of mass of 
//       appropriately coloured pixels
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef COLOUR_TRACKER_H
#define COLOUR_TRACKER_H

//------------------------------------------------------------------------------
struct _IplImage;

//------------------------------------------------------------------------------
class BlobData
{
    public: BlobData() {}
    public: BlobData( bool bVisible, float centreX, float centreY, float radius );

    public: bool mbVisible;
    public: float mCentreX;
    public: float mCentreY;
    public: float mRadius;
};

//------------------------------------------------------------------------------
class ColourTracker
{
    public: ColourTracker( float trackedHue = DEFAULT_TRACKED_HUE, 
        float maxAbsHueDiff = DEFAULT_MAX_ABS_HUE_DIFF, bool bCalculateRadius = DEFAULT_CALCULATE_RADIUS );

    public: void Reset();
    public: void ProcessFrame( const _IplImage* pFrame );

    public: const BlobData& GetBlobData() const { return mBlobData; }

    private: BlobData mBlobData;
    private: float mTrackedHue;
    private: float mMaxAbsHueDiff;
    private: bool mbCalculateRadius;

    public: static const float DEFAULT_TRACKED_HUE;
    public: static const float DEFAULT_MAX_ABS_HUE_DIFF;
    public: static const bool DEFAULT_CALCULATE_RADIUS;
};

#endif // COLOUR_TRACKER_H
