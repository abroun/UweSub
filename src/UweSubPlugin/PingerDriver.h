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
#include "DataStructures/PICPacket.h"
#include "DataStructures/PICComm.h"
#include "DataStructures/picmsgs.h"

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
    
    private: void flushSerialBuffer();
    
    private: void transitionAction(PICPacket* pack);
    
    private: F32 calcAngularVelocity(U32 analog);
    
    private: F32 calcAcceleration(U32 analog);
    
    private: F32 locateObstacle(U8* data);
    
    private: U32 observeEcho(U8* data);
    
    // Properties
    private: IntProperty mBufferSize;
    
    // Link to the communication stream
    private: Device* mpOpaque;
    private: player_devaddr_t mOpaqueID;
    
    private: RollingBuffer mBuffer;
    
    public: U8 state;
    
    // globals for handling serial incoming
    private: int remainingBytes;
    private: U8 bufhead[7];
    
    private: static const U32 DEFAULT_BUFFER_SIZE;
    private: static const U16 DATA_PACKET_ID;
    // state constants
    public: static const U8 stIdle=0;
    public: static const U8 stWaitingAcceleration = 1;
    public: static const U8 stWaitingAngVelocity = 2;
    public: static const U8 stWaitingPassiveEcho= 3;
    public: static const U8 stWaitingActiveECho = 4;
    // state constants ends

};

//------------------------------------------------------------------------------
void PingerDriverRegister( DriverTable* pTable );

#endif // PINGER_DRIVER_H
