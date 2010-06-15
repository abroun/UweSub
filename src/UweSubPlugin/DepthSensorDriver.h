//------------------------------------------------------------------------------
// File: DepthSensorDriver.h
// Desc: A simple serial relay for data being sent from a depth sensor attached
//       to an Arduino. We would control the sensor directly from the RoBoard 
//       but the SPI on the RoBoard is too fast... :P
//
// Usage Example:
//
//  driver
//  (
//    name "depthsensordriver"
//    provides ["position1d:0"]
//    requires ["opaque:0"]
//    buffer_size 512
//  )
//
//  driver
//  (
//    name "serialstream"
//    provides ["opaque:0"]
//    port "/dev/ttyS0"
//  )
//
//
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef DEPTH_SENSOR_DRIVER_H
#define DEPTH_SENSOR_DRIVER_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>
#include "Common.h"
#include "DataStructures/RollingBuffer.h"

//------------------------------------------------------------------------------
class DepthSensorDriver : public ThreadedDriver
{
    typedef ThreadedDriver base;
    
    // Constructor/Destructor
    public: DepthSensorDriver( ConfigFile* pConfigFile, int section );
    public: virtual ~DepthSensorDriver();

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
    
    // Helper routine that calcuates the CRC value for a block of data
    private: U16 CalculateCRC( U8* pData, U32 numBytes );

    // Properties
    private: IntProperty mBufferSize;
    
    // Link to the communication stream
    private: Device* mpOpaque;
    private: player_devaddr_t mOpaqueID;
    
    private: RollingBuffer mBuffer;
    
    private: static const U32 DEFAULT_BUFFER_SIZE;
    private: static const U16 DATA_PACKET_ID;

};

//------------------------------------------------------------------------------
void DepthSensorDriverRegister( DriverTable* pTable );

#endif // DEPTH_SENSOR_DRIVER_H
