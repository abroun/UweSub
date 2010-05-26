//------------------------------------------------------------------------------
// File: SonarDriver.cpp
// Desc: A driver for controlling a Tritech Micron Sonar
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include "SonarDriver.h"

//------------------------------------------------------------------------------
// A factory creation function, declared outside of the class so that it
// can be invoked without any object context (alternatively, you can
// declare it static in the class).  In this function, we create and return
// (as a generic Driver*) a pointer to a new instance of this driver.
Driver* SonarDriverInit( ConfigFile* pConfigFile, int section )
{
    // Create and return a new instance of this driver
    return (Driver*)(new SonarDriver( pConfigFile, section ));
}

//------------------------------------------------------------------------------
// A driver registration function, again declared outside of the class so
// that it can be invoked without object context.  In this function, we add
// the driver into the given driver table, indicating which interfaces the
// driver can support and how to create a driver instance.
void SonarDriverRegister( DriverTable* pTable )
{
    pTable->AddDriver( (char*)"sonardriver", SonarDriverInit );
}

//------------------------------------------------------------------------------
// SonarDriver
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// Constructor.  Retrieve options from the configuration file and do any
// pre-Setup() setup.
SonarDriver::SonarDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_CAMERA_CODE )
{
    this->alwayson = true;
    
}

//------------------------------------------------------------------------------
SonarDriver::~SonarDriver()
{
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int SonarDriver::MainSetup()
{
    return 0;
}


//------------------------------------------------------------------------------
// Shutdown the device
void SonarDriver::MainQuit()
{
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int SonarDriver::ProcessMessage( QueuePointer& respQueue,
                                player_msghdr* pHeader, void* pData )
{   
    
    printf( "Unhandled message\n" );
    return -1;
}

//------------------------------------------------------------------------------
// Main function for device thread
void SonarDriver::Main()
{
    for (;;)
    {
        // Wait for messages to arrive
        base::Wait();
        
        base::ProcessMessages();
    }
}

