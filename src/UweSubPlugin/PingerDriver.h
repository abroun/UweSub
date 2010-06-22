//------------------------------------------------------------------------------
// File: PingerDriver.h
// Desc: A driver to communicate with George's custom sonar hardware
//
// Usage Example:
//
//  driver
//  (
//    name "pingerdriver"
//    provides ["speech:0"]
//    requires ["opaque:0"]
//    buffer_size 10000
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
#ifndef PINGER_DRIVER_H
#define PINGER_DRIVER_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>
#include "Common.h"
#include "DataStructures/RollingBuffer.h"

//------------------------------------------------------------------------------
class PingerDriver : public ThreadedDriver
{
    typedef ThreadedDriver base;
    
    // Constructor/Destructor
    public: PingerDriver( ConfigFile* pConfigFile, int section );
    public: virtual ~PingerDriver();

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
void PingerDriverRegister( DriverTable* pTable );

#endif // PINGER_DRIVER_H
