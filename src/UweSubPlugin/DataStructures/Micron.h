 
#ifndef MICRON_H
#define MICRON_H
 
#include "TritecPacket.h"
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <math.h>
#include "Common.h"
#include <libplayercore/playercore.h>
#include "Common/HighPrecisionTime.h"


    
class Micron {

    public: static const F32 DEFAULT_GAIN;
    public: static const S32 MAX_SONAR_ANGLE = 6400;  // In 1/16 Grads
    public: static const S32 SONAR_STEP_ANGLE = 16; // In 1/16 Grads
    public: static const S32 MIN_NUM_BINS = 1;
    public: static const S32 MAX_NUM_BINS = 1500;
    public: static const S32 MIN_RANGE;
    public: static const S32 MAX_RANGE;
    public: static const S32 MIN_AD_INTERVAL;  // In units of 640ns
    
    
    public: struct ScanSettings
    {
        S32 mRange;         // In metres
        S32 mStartAngle;    // In 1/16 Grads
        S32 mEndAngle;      // In 1/16 Grads
        S32 mNumBins;
        S32 mStepAngle;      // In 1/16 Grads
        
        //----------------------------------------------------------------------
        // mEndAngle = (mStartAngle + GetAngleDiff())%MAX_SONAR_ANGLE;
        S32 GetAngleDiff() const 
        {
            S32 angleDiff = mEndAngle - mStartAngle;
            while ( angleDiff < 0 )   // Get the difference as a +ve value
            {
                angleDiff += MAX_SONAR_ANGLE;
            }
            
            return angleDiff;
        }
    };
    
    public: struct Ray
    {
        U8 mBins[ MAX_NUM_BINS ];
        U16 mNumBins;
    };
    
    // Careful when creating an instance of ScanData, it probably
    // weighs in at about quater of a megabyte at the moment...
    public: struct ScanData
    {
        // Clears out all data
        void clear();
        
        static const S32 MAX_NUM_RAYS = MAX_SONAR_ANGLE/SONAR_STEP_ANGLE;
        Ray mRays[ MAX_NUM_RAYS ];
        S32 mNumRaysScanned;
        ScanSettings mSettings; // The settings used for this scan
    };
    
       // Tritec Protocol Command Constants
       private: static const U8 mtVersionData; // Version reply by the micron
       private: static const U8 mtHeadData; // Head data reply by the micron
       private: static const U8 mtAlive;    // Alive reply by the micron
       private: static const U8 mtBBUserData; // User data reply by the micron
       private: static const U8 mtReBoot; // Reboot sonar
       private: static const U8 mtHeadCommand; // configure the micron for scanning
       private: static const U8 mtSendVersion;  // request parameters from micron
       private: static const U8 mtSendBBUser; // request user data from micron
       private: static const U8 mtSendData;   // request half/full duplex data from micron
       private: static const U8 mtStopAlive; // forces micron to stop sedning repeated alive msgs
        
       // Commands ends

       // Operation constants
       public: enum eRegion
       {
           eR_Left,         // 135 to 225 degrees
           eR_Front,        //45 to 135 degrees 
           eR_Right,        // -45 to 45 degrees
           eR_RearLeft,     // 235 to 270 degrees
           eR_RearRight,     // 270 to 315 degrees
           eR_Full,          // 0 to 360
       };
       
       // alive constants (for evaluation of an mtAlive Message)
       public: static const U8 alFalseAlive;
       public: static const U8 alNoParams;
       public: static const U8 alParamsAck;
       public: static const U8 alInScan;

       // class members
       private: int state;
                S32 mRange;
                S32 mNumBins;
                S32 mADlow;
                S32 mADspan;
                F32 mGain;    // Gain from 0.0 to 1.0
                S32 mStartAngle;
                S32 mEndAngle;
                ScanData mScanData;    // Data retrieved from the sonar
                HighPrecisionTime mLastDataRequestTime;

       // state constants
       public: static const int stIdle;
       public: static const int stConnected;
       public: static const int stExpectAlive;
       public: static const int stAliveSonar;
       public: static const int stExpectHeadAlive;
       public: static const int stSendingData;
       public: static const int stExpectHeadData;
       public: static const int stExpectUserData;
       public: static const int stDataReady;
  
     
  
                // parametric constructor
        public: Micron(int range, int resolution, int ADlow, int ADspan);
        
                // default values constructor
                Micron();
        
                // Micron Destructor
                ~Micron(); 
    
         // a method to reset the micron to it's default (must be used after a reboot)
        public: void reset();
         
        // ******** The following functions send packages to the micron via a designated channel (use of opaque)******
        
       // send BB user Data 
       public: void sendBBUser(Device* theOpaque, QueuePointer inqueue);
        
        // this function kills the constant alive messages from the micron
        public: void sendStopAlives(Device* theOpaque, QueuePointer inqueue); 
        
       
        //this function reboots the micron
        public: void sendReboot(Device* theOpaque, QueuePointer inqueue);
        

        // this function sends an mtSendVersion command
        public: void sendVersion(Device* theOpaque, QueuePointer inqueue);
      

        // this function sends an mtHeadCommand
        public: void sendHeadCommand( Device* theOpaque, QueuePointer inqueue );
        

        // this functions sends a sendData command
        public: void sendData(Device* theOpaque, QueuePointer inqueue);
        
        // **************************** Send Package Functions ends here ********************************

        // **************************** Internal Class State and Data Handling ************************** 
        
        // this function changes internal state
        public: virtual void transitionAction(TritecPacket* pack, Device* theOpaque, QueuePointer inqueue);
        

        // ************************ State and Data Handling functions ends here **************************
        
        // this function returns the total length of a packet in bytes
        public: static int packetLength(TritecPacket* tp);
        
        // This function converts a packet to a raw bytes message
        public: static U8* convertPacket2Bytes(TritecPacket* tp);
    
        // This function makes a packet out of raw bytes
        public: static TritecPacket* convertBytes2Packet(U8* msg);
        
        // This function disposes a tritech Packet
        public: static void disposePacket(TritecPacket* pack);

    // ************************* Methods that create micron command packets ********************    

        // mtReboot Command Packet
        public: static TritecPacket* makeReboot();
        
       // mtSendVesrion Command packet
        public: static TritecPacket* makeSendVersion();

        // mtStopAlives command packet
        public: static TritecPacket* makeStopAlives();
        
         // mtSendData command packet
        public: static TritecPacket* makeSendData();
    
         // mtHeadData command packet.
         // Warning: No real checking is done on routines arguments to check
         // that it's valid, data is simply packed up. Therefore it should
         // only be used with extreme care by code outside the Micron class
        public: static TritecPacket* makeHead( int range, S32 numBins, 
            int startAngle, int endAngle,
            int ADlow, int ADspan, F32 gain, ScanSettings* pScanSettingsOut = NULL );
        
        // An mtSendBBUser command packet
        public: static TritecPacket* makeSendBBUser();
    // **************************** Command Packets Methods ends here ********************************


    // ******************************** Packet Handling methods **************************************

    // This function returns a scanned line as an array of characters from a HeadData packet        
    public: static U8* unwrapHeadData(TritecPacket* hdatapack, int* pDataLenOut, int* pTransducerAngleOut );
        
    // This function recognizes the type of an alive message returned by the micron
        public: static int validateAlive(TritecPacket* alivepack);
    // Packet Handling methods ends here     
    
    // member variable methods
    public: void setState(int state);
    public: int getState();
    
    public: void setRegion(eRegion region);
    public: void setAngleRange( S32 startAngle, S32 endAngle );
    public: S32 getStartAngle() const { return mStartAngle; }
    public: S32 getEndAngle() const { return mEndAngle; }
    
    public: void setResolution(int resolution);
    public: int getResolution() const;
    public: void setNumBins( S32 numBins );
    public: S32 getNumBins() const { return mNumBins; }
     
    public: void setRange(int range);
    public: int getRange();
    
    public: void setRangeAndResolution( S32 range, S32 resolution );
    public: void setRangeAndNumBins( S32 range, S32 numBins );
    
    public: void setADlow(int adlow);
    public: int getADlow();
    
    public: void setADspan(int adspan);
    public: int getADspan();
    
    public: void setGain( F32 gain );
    public: F32 getGain() const;
    
    public: HighPrecisionTime GetLastDataRequestTime() const { return mLastDataRequestTime; }

    public: const ScanData* getScanData() const { return &mScanData; }
    
    public: void printState();
    
    private: static S32 calculateADInterval( S32 range, S32 numBins );
    
    public: static S32 convertResolutionToNumBins( S32 range, S32 resolution );
    public: static S32 convertNumBinsToResolution( S32 range, S32 numBins );
    public: static F32 convertSonarAngleToRadians( S32 angle )
    {
        return (F32)(((F32)angle / (F32)MAX_SONAR_ANGLE)*2.0f*M_PI);
    }
    public: static S32 convertRadiansToSonarAngle( F32 rads )
    {
        return (S32)((rads/(2.0f*(F32)M_PI)) * MAX_SONAR_ANGLE);
    }
    // member variable methods done
    

        
 }; // class definition ends here 

#endif // Header ends here
