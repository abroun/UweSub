//------------------------------------------------------------------------------
// File: SonarDriver.cpp
// Desc: A driver for controlling a Tritech Micron Sonar
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include "SonarDriver.h"

#include <assert.h> // For RollingBuffer

//------------------------------------------------------------------------------
// RollingBuffer
//------------------------------------------------------------------------------
RollingBuffer::RollingBuffer( U32 bufferSize )
{
    mpBuffer = (U8*)malloc( bufferSize );
    assert( NULL != mpBuffer && "Unable to allocate buffer" );
    
    mBufferSize = bufferSize;
    mDataStartIdx = 0;
    mDataSize = 0;
}

//------------------------------------------------------------------------------
RollingBuffer::~RollingBuffer()
{
    if ( NULL != mpBuffer )
    {
        free( mpBuffer );
        mpBuffer = NULL;
    }
}
    
//------------------------------------------------------------------------------
void RollingBuffer::Clear()
{
    mDataStartIdx = 0;
    mDataSize = 0;
}
    
//------------------------------------------------------------------------------
U32 RollingBuffer::ReadBytes( U8* pDataOut, U32 numBytes )
{
    U32 numBytesRead = PeekAtBytes( pDataOut, numBytes );
    AdvanceBuffer( numBytesRead );
    
    return numBytesRead;
}
    
//------------------------------------------------------------------------------
U32 RollingBuffer::PeekAtBytes( U8* pDataOut, U32 numBytes ) const
{
    assert( NULL != pDataOut );
    
    U32 numBytesRead = numBytes;
    if ( numBytesRead > mDataSize )
    {
        numBytesRead = mDataSize;
    }
    
    // Test to see if we can do the read all in one go
    U32 numContiguousBytesAvailable = mBufferSize - mDataStartIdx;
    if ( numContiguousBytesAvailable >= numBytesRead )
    {
        memcpy( pDataOut, &mpBuffer[ mDataStartIdx ], numBytesRead );
    }
    else
    {
        // The read has to be done in 2 parts
        memcpy( pDataOut, &mpBuffer[ mDataStartIdx ], numContiguousBytesAvailable );
        
        U32 numBytesRemaining = numBytesRead - numContiguousBytesAvailable;
        memcpy( &pDataOut[ numContiguousBytesAvailable ],
                &mpBuffer[ 0 ], numBytesRemaining );
    }
    
    return numBytesRead;
    
}
    
//------------------------------------------------------------------------------
void RollingBuffer::AdvanceBuffer( U32 numBytes )
{
    U32 bytesToAdvance = numBytes;
    if ( bytesToAdvance > mDataSize )
    {
        bytesToAdvance = mDataSize;
    }
    
    mDataStartIdx = AddOffsetToIdx( mDataStartIdx, bytesToAdvance );
    mDataSize -= bytesToAdvance;
}
    
//------------------------------------------------------------------------------
bool RollingBuffer::TryToAddBytes( U8* pData, U32 numBytes )
{
    bool bBytesAdded = false;
    
    if ( numBytes < GetFreeSpace() )
    {
        // Test to see if we can write the data all in one go
        U32 endOfDataIdx = AddOffsetToIdx( mDataStartIdx, mDataSize );
        U32 numContiguousBytesAvailable = mBufferSize - endOfDataIdx;
        if ( numContiguousBytesAvailable >= numBytes )
        {
            memcpy( &mpBuffer[ endOfDataIdx ], pData, numBytes );
        }
        else
        {
            // The write has to be done in 2 parts
            memcpy( &mpBuffer[ endOfDataIdx ], pData, numContiguousBytesAvailable );
            
            U32 numBytesRemaining = numBytes - numContiguousBytesAvailable;
            memcpy( &mpBuffer[ 0 ], 
                    &pData[ numContiguousBytesAvailable ], numBytesRemaining );
        }
        
        mDataSize += numBytes;
        bBytesAdded = true;
    }
    
    return bBytesAdded;
}

//------------------------------------------------------------------------------
U32 RollingBuffer::AddOffsetToIdx( U32 idx, U32 offset ) const
{
    U32 numBytesToEnd = mBufferSize - idx;
    if ( offset < numBytesToEnd )
    {
        return idx + offset;
    }
    else
    {
        // Wrap around and start from the beginning of the buffer
        return offset - numBytesToEnd;
    }
}

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

