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
    // ColourTracker initially tracks a given hue. If more control is required then the 
    // saturation and value can be tracked as well
    public: ColourTracker( float trackedHue = DEFAULT_TRACKED_HUE, 
        float maxAbsHueDiff = DEFAULT_MAX_ABS_HUE_DIFF, bool bCalculateRadius = DEFAULT_CALCULATE_RADIUS );

    public: void Reset();
    public: _IplImage* ProcessFrame( const _IplImage* pFrame );

    public: const BlobData& GetBlobData() const { return mBlobData; }
    
    // Specify the tracked hue in the range [0.0, 360.0). A negative number means that hue is not tracked
    public: void SetTrackedHue( float trackedHue, float maxAbsHueDiff = DEFAULT_MAX_ABS_HUE_DIFF );
    // Specify the tracked saturation in the range [0.0, 100.0]. A negative number means that saturation is not tracked
    public: void SetTrackedSaturation( float trackedSaturation, float maxAbsSaturationDiff = DEFAULT_MAX_ABS_SATURATION_DIFF );
    // Specify the tracked value in the range [0.0, 100.0]. A negative number means that value is not tracked
    public: void SetTrackedValue( float trackedValue, float maxAbsValueDiff = DEFAULT_MAX_ABS_VALUE_DIFF );

    private: BlobData mBlobData;
    private: float mTrackedHue;
    private: float mMaxAbsHueDiff;
    private: float mTrackedSaturation;
    private: float mMaxAbsSaturationDiff;
    private: float mTrackedValue;
    private: float mMaxAbsValueDiff;
    private: bool mbCalculateRadius;

    public: static const float MAX_HUE;
    public: static const float MAX_SATURATION;
    public: static const float MAX_VALUE;
    public: static const float OPENCV_MAX_HUE;
    public: static const float OPENCV_MAX_SATURATION;
    public: static const float OPENCV_MAX_VALUE;
    
    public: static const float DEFAULT_TRACKED_HUE;
    public: static const float DEFAULT_MAX_ABS_HUE_DIFF;
    public: static const float DEFAULT_TRACKED_SATURATION;
    public: static const float DEFAULT_MAX_ABS_SATURATION_DIFF;
    public: static const float DEFAULT_TRACKED_VALUE;
    public: static const float DEFAULT_MAX_ABS_VALUE_DIFF;
    public: static const bool DEFAULT_CALCULATE_RADIUS;
};

#endif // COLOUR_TRACKER_H
