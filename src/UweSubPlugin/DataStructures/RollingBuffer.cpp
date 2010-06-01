//------------------------------------------------------------------------------
// File: RollingBuffer.cpp
// Desc: A simple rolling buffer implemented using a fixed size array
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "RollingBuffer.h"

//------------------------------------------------------------------------------
// RollingBuffer
//------------------------------------------------------------------------------
RollingBuffer::RollingBuffer()
    : mpBuffer( NULL ),
    mBufferSize( 0 ),
    mDataStartIdx( 0 ),
    mDataSize( 0 )
{  
}

//------------------------------------------------------------------------------
RollingBuffer::~RollingBuffer()
{
    Deinit();
}

//------------------------------------------------------------------------------
bool RollingBuffer::Init( U32 bufferSize )
{
    mpBuffer = (U8*)malloc( bufferSize );
    bool bBufferAllocated = ( NULL != mpBuffer );
    assert( bBufferAllocated && "Unable to allocate buffer" );
    
    if ( bBufferAllocated )
    {
        mBufferSize = bufferSize;
        mDataStartIdx = 0;
        mDataSize = 0;
    }
    
    return bBufferAllocated;
}

//------------------------------------------------------------------------------
void RollingBuffer::Deinit()
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
bool RollingBuffer::TryToAddBytes( const U8* pData, U32 numBytes )
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