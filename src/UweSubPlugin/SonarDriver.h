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

//------------------------------------------------------------------------------
class SonarDriver : public ThreadedDriver
{
    typedef ThreadedDriver base;
    
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
};

//------------------------------------------------------------------------------
void SonarDriverRegister( DriverTable* pTable );

#endif // SONAR_DRIVER_H
