//------------------------------------------------------------------------------
// File: CompassDriver.h
// Desc: A driver for controlling a PNI Compass
//
// Usage Example:
//
//  driver
//  (
//    name "compassdriver"
//    provides ["imu:0"]
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
#ifndef COMPASS_DRIVER_H
#define COMPASS_DRIVER_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>
#include "Common.h"
#include "DataStructures/RollingBuffer.h"

//------------------------------------------------------------------------------
class CompassDriver : public ThreadedDriver
{
    typedef ThreadedDriver base;
    
    // Constructor/Destructor
    public: CompassDriver( ConfigFile* pConfigFile, int section );
    public: virtual ~CompassDriver();

    // Set up the driver.  Return 0 if things go well, and -1 otherwise.
    public: virtual int MainSetup();

    // Shutdown the device
    public: virtual void MainQuit();

    // Process all messages for this driver. 
    public: virtual int ProcessMessage( QueuePointer& respQueue, 
                                        player_msghdr* pHeader, 
                                        void* pData );
                                        
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
};

//------------------------------------------------------------------------------
void CompassDriverRegister( DriverTable* pTable );

#endif // COMPASS_DRIVER_H
