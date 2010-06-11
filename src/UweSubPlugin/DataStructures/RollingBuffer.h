//------------------------------------------------------------------------------
// File: RollingBuffer.h
// Desc: A simple rolling buffer implemented using a fixed size array
//------------------------------------------------------------------------------
 
//------------------------------------------------------------------------------
#ifndef ROLLING_BUFFER_H
#define ROLLING_BUFFER_H

//------------------------------------------------------------------------------
#include "Common.h"

//------------------------------------------------------------------------------
class RollingBuffer
{
    // Constructor/Destructor
    public: RollingBuffer();
    public: ~RollingBuffer();
    
    public: bool Init( U32 bufferSize );
    public: void Deinit();
    
    // Information about the buffer
    public: U32 GetSize() const { return mBufferSize; }
    public: U32 GetNumBytesInBuffer() const { return mDataSize; }
    public: U32 GetFreeSpace() const { return mBufferSize - mDataSize; }
    
    // Clears all data from the buffer
    public: void Clear();
    
    // Reads data from the buffer and advances the read pointer.
    // Returns the number of bytes that were actually read.
    public: U32 ReadBytes( U8* pDataOut, U32 numBytes );
    
    // Similar to ReadBytes but doesn't advance the buffer
    // Returns the number of bytes that were actually read.
    public: U32 PeekAtBytes( U8* pDataOut, U32 numBytes ) const;
    
    // Advances the read pointer by at most numBytes
    public: void AdvanceBuffer( U32 numBytes );
    
    // Attempts to add numBytes of data to the buffer. If there isn't
    // enough space in the buffer then it returns false. Otherwise it
    // returns true.
    public: bool TryToAddBytes( const U8* pData, U32 numBytes );
    
    // Helper routine for making sure that indicies stay within the buffer
    private: U32 AddOffsetToIdx( U32 idx, U32 offset ) const;
    
    // Member variables
    private: U8* mpBuffer;
    private: U32 mBufferSize;
    private: U32 mDataStartIdx;
    private: U32 mDataSize;
};

#endif // ROLLING_BUFFER_H