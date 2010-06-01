//------------------------------------------------------------------------------
// File: SonarDriver.cpp
// Desc: A driver for controlling a Tritech Micron Sonar
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include <assert.h>
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
const U32 SonarDriver::DEFAULT_BUFFER_SIZE = 10000;

//------------------------------------------------------------------------------
// Constructor.  Retrieve options from the configuration file and do any
// pre-Setup() setup.
SonarDriver::SonarDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_CAMERA_CODE ),
    mBufferSize( "buffer_size", DEFAULT_BUFFER_SIZE, false )
{
    this->alwayson = true;
    
    mpOpaque = NULL;
    // We must have an opaque device
    if ( pConfigFile->ReadDeviceAddr( &mOpaqueID, section, "requires",
                       PLAYER_OPAQUE_CODE, -1, NULL ) != 0 )
    {
        PLAYER_ERROR( "No Opaque driver specified" );
        SetError(-1);
        return;
    }
    
    // Read options from the configuration file
    RegisterProperty( "buffer_size", &mBufferSize, pConfigFile, section );

    mBuffer.Init( mBufferSize.GetValue() );
}

//------------------------------------------------------------------------------
SonarDriver::~SonarDriver()
{
    mBuffer.Deinit();
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int SonarDriver::MainSetup()
{
    PLAYER_WARN( "Setting up Sonar driver" );

    if ( Device::MatchDeviceAddress( mOpaqueID, this->device_addr ) )
    {
        PLAYER_ERROR( "Attempting to subscribe to self" );
        return -1;
    }

    mpOpaque = deviceTable->GetDevice( mOpaqueID );
    if ( NULL == mpOpaque )
    {
        PLAYER_ERROR( "Unable to locate suitable opaque device" );
        return -1;
    }

    if ( mpOpaque->Subscribe( this->InQueue ) != 0 )
    {
        PLAYER_ERROR( "Unable to subscribe to opaque device" );
        return -1;
    }

    // Code to send a message
    //uint8_t* buffer = new uint8_t[MESSAGE_LEN];
    //assert(buffer);
    //makeStartStopCommand(buffer, true);
    //player_opaque_data_t mData;
    //mData.data_count = MESSAGE_LEN;
    //mData.data = buffer;

    //mpOpaque->PutMsg( this->InQueue, 
    //    PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, 
    //    reinterpret_cast<void*>(&mData), 0, NULL );

    //delete [] buffer;
    //buffer = NULL;

    PLAYER_WARN( "Sonar driver ready" );

    return 0;
}

//------------------------------------------------------------------------------
// Shutdown the device
void SonarDriver::MainQuit()
{
    PLAYER_WARN( "Sonar driver shutting down");

    mpOpaque->Unsubscribe( this->InQueue );

    PLAYER_WARN( "Sonar driver has been shutdown" );
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int SonarDriver::ProcessMessage( QueuePointer& respQueue,
                                player_msghdr* pHeader, void* pData )
{   
    if ( Message::MatchMessage(
        pHeader, PLAYER_MSGTYPE_DATA, PLAYER_OPAQUE_DATA_STATE, mOpaqueID ) )
    {
        player_opaque_data_t* pOpaqueData = (player_opaque_data_t*)pData;
        
        if ( pOpaqueData->data_count <= mBuffer.GetFreeSpace() )
        {
            mBuffer.TryToAddBytes( pOpaqueData->data, pOpaqueData->data_count );
        }
        else
        {
            PLAYER_WARN( "Sonar driver buffer is full. Dropping data" );
        }
        return 0;
    }
    
    PLAYER_WARN( "Unhandled message\n" );
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
        
        ProcessData();
    }
}

//------------------------------------------------------------------------------
void SonarDriver::ProcessData()
{
    const S32 MAX_STRING_LENGTH = 1024;
    U8 stringBuffer[ MAX_STRING_LENGTH + 1 ];
    
    while ( mBuffer.GetNumBytesInBuffer() > 0 )
    {
        U32 numBytesToRead = mBuffer.GetNumBytesInBuffer();
        if ( numBytesToRead > MAX_STRING_LENGTH )
        {
            numBytesToRead = MAX_STRING_LENGTH;
        }
        
        mBuffer.ReadBytes( stringBuffer, numBytesToRead );
        stringBuffer[ numBytesToRead ] = '\0';
        
        printf( "%s", stringBuffer );
    }
}
