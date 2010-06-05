//------------------------------------------------------------------------------
// File: DepthSensorDriver.cpp
// Desc: A driver for controlling an Intersema depth sensor over SPI
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include <assert.h>
#include "DepthSensorDriver.h"
#include "Common/HighPrecisionTime.h"
#include "Common/Utils.h"
#include "roboard.h"
#include "spi.h"

//------------------------------------------------------------------------------
// A factory creation function, declared outside of the class so that it
// can be invoked without any object context (alternatively, you can
// declare it static in the class).  In this function, we create and return
// (as a generic Driver*) a pointer to a new instance of this driver.
Driver* DepthSensorDriverInit( ConfigFile* pConfigFile, int section )
{
    // Create and return a new instance of this driver
    return (Driver*)(new DepthSensorDriver( pConfigFile, section ));
}

//------------------------------------------------------------------------------
// A driver registration function, again declared outside of the class so
// that it can be invoked without object context.  In this function, we add
// the driver into the given driver table, indicating which interfaces the
// driver can support and how to create a driver instance.
void DepthSensorDriverRegister( DriverTable* pTable )
{
    pTable->AddDriver( (char*)"depthsensordriver", DepthSensorDriverInit );
}

//------------------------------------------------------------------------------
// DepthSensorDriver
//------------------------------------------------------------------------------
DepthSensorDriver::DepthSensorDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_POSITION1D_CODE ),
    mbInitialisedSPI( false )
{
    this->alwayson = true;
}

//------------------------------------------------------------------------------
DepthSensorDriver::~DepthSensorDriver()
{
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int DepthSensorDriver::MainSetup()
{
    mbInitialisedSPI = spi_Initialize( SPICLK_10000KHZ );
    
    return 0;
}

//------------------------------------------------------------------------------
// Shutdown the device
void DepthSensorDriver::MainQuit()
{
    spi_Close();
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int DepthSensorDriver::ProcessMessage( QueuePointer& respQueue,
                                player_msghdr* pHeader, void* pData )
{   
    PLAYER_WARN( "Unhandled message\n" );
    return -1;
}

//------------------------------------------------------------------------------
// Main function for device thread
void DepthSensorDriver::Main()
{
    HighPrecisionTime sleepTime = HighPrecisionTime::ConvertFromSeconds( 0.1 );
    
    for (;;)
    {
        base::ProcessMessages();
        
        Utils::Sleep( sleepTime );
        if ( mbInitialisedSPI )
        {
            spi_WriteFlush( 0x10 );
            U32 result = spi_Read();
            printf( "Depth is %i\n", result );
        }
        else
        {
            printf( "Depth is unknown\n" );
        }
    }
}

