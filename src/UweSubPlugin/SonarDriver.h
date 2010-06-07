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
    private: char* bufhead;
};

//------------------------------------------------------------------------------
void SonarDriverRegister( DriverTable* pTable );

#endif // SONAR_DRIVER_H
