//------------------------------------------------------------------------------
// File: SonarDriver.h
// Desc: A driver for controlling a Tritech Micron Sonar
//
// Usage Example:
// 
//  driver
//  (
//    name "sonardriver"
//    provides ["camera:1"]
//    requires ["opaque:0"]
//    buffer_size 20480
//  )
//
//  driver
//  (
//    name "serialstream"
//    provides ["opaque:0"]
//    port "/dev/ttyS0"
//  )
//
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef SONAR_DRIVER_H
#define SONAR_DRIVER_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>
#include "Common.h"
#include "DataStructures/RollingBuffer.h"
#include "DataStructures/Micron.h"
#include "DataStructures/microncmds.h"

//------------------------------------------------------------------------------
class SonarDriver : public ThreadedDriver
{ 
    typedef ThreadedDriver base;
    
    // member Micron class
    private: Micron* pmicron;
    
   
    
    // Constructor/Destructor
    public: SonarDriver( ConfigFile* pConfigFile, int section );
    public: virtual ~SonarDriver();

    // Set up the driver.  Return 0 if things go well, and -1 otherwise.
    public: virtual int MainSetup();

    // Shutdown the device
    public: virtual void MainQuit();

    // Process all messages for this driver. 
    public: virtual int ProcessMessage( QueuePointer& respQueue, 
                                        player_msghdr* pHeader, 
                                        void* pData );
    
    // clear residual data in the Rolling buffer
    public: void flushSerialBuffer();
    // The main routine of the thread
    private: virtual void Main();
    
    private: void ProcessData();
    
    
    // Properties
    private: IntProperty mBufferSize;
    
    // Link to the communication stream
    private: Device* mpOpaque;
    private: player_devaddr_t mOpaqueID;
    
    private: RollingBuffer mBuffer;
    
    private: static const U32 DEFAULT_BUFFER_SIZE;
    
    // globals for handling serial incoming
    private: int remainingBytes;
    private: U8 bufhead[7];
    
    // ************************** Sonar image handling methods ***************************************
    
    // This function assigns the various bins to their position in the map array (each cell is 1cmx1cm)
    // preferably, map dimention should be 2*arange*100+1 
    // (ipos, jpos) is the position of the sonar in the grid to be updated (suggested, ipos = jpos = arange*100)
    // specify resolution in cms, range in meters
    // startangle and endangle in degrees in counter-clockwise fashion
    // abins should be the array of bins produced by the micron class
    public: static void polar2Cartesian(U8** amap, const Micron::ScanData* pScanData, U32 ipos, U32 jpos);
    
    // The following method normalizes the contents of a grid map
    // using a normal distribution of sigma^2 standard deviation (diaspora is sigma)
    public: static void mapNormalization(U8* amap[], U32 dim, F32 sigma);
    
    public: static void mapAutothreshold(U8* amap[], U32 dim, U8 threshold);
    
    // *************** Sonar image handling functions ends here ***********************************

    
};

//------------------------------------------------------------------------------
void SonarDriverRegister( DriverTable* pTable );

#endif // SONAR_DRIVER_H
