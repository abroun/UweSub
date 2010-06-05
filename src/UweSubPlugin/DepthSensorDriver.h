//------------------------------------------------------------------------------
// File: DepthSensorDriver.h
// Desc: A driver for controlling an Intersema depth sensor over SPI
//
// Usage Example:
//
//  driver
//  (
//    name "depthsensordriver"
//    provides [":0"]
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
    
    private: bool mbInitialisedSPI;
};

//------------------------------------------------------------------------------
void DepthSensorDriverRegister( DriverTable* pTable );

#endif // DEPTH_SENSOR_DRIVER_H
