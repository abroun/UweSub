//------------------------------------------------------------------------------
// File: DepthSensorDriver.cpp
// Desc: A simple serial relay for data being sent from a depth sensor attached
//       to an Arduino. We would control the sensor directly from the RoBoard 
//       but the SPI on the RoBoard is too fast... :P
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include <assert.h>
#include "DepthSensorDriver.h"
#include "Common/HighPrecisionTime.h"

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
// Helper routines for reading data types from a buffer. These assume that we're 
// reading little-endian data into little-endian data types
static inline U16 READ_U16( U8* buffer )
{
    return *(U16*)buffer;
}

static inline U32 READ_U32( U8* buffer )
{
    return *(U32*)buffer;
}

static inline S32 READ_S32( U8* buffer )
{
    return (S32)READ_U32( buffer );
}

static inline F32 READ_F32( U8* buffer )
{
    U32 floatData = READ_U32( buffer );
    return *((F32*)&floatData);
}

//------------------------------------------------------------------------------
// DepthSensorDriver
//------------------------------------------------------------------------------
const U32 DepthSensorDriver::DEFAULT_BUFFER_SIZE = 512;
const U16 DepthSensorDriver::DATA_PACKET_ID = 0xDEAB;

//------------------------------------------------------------------------------
DepthSensorDriver::DepthSensorDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_POSITION1D_CODE ),
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
DepthSensorDriver::~DepthSensorDriver()
{
    mBuffer.Deinit();
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int DepthSensorDriver::MainSetup()
{
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
    
    return 0;
}

//------------------------------------------------------------------------------
// Shutdown the device
void DepthSensorDriver::MainQuit()
{
    mpOpaque->Unsubscribe( this->InQueue );
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int DepthSensorDriver::ProcessMessage( QueuePointer& respQueue,
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
            PLAYER_WARN( "Depth Sensor driver buffer is full. Dropping data" );
        }
        return 0;
    }
    
    PLAYER_WARN( "Unhandled message\n" );
    return -1;
}

//------------------------------------------------------------------------------
// Main function for device thread
void DepthSensorDriver::Main()
{
    HighPrecisionTime oldTime = HighPrecisionTime::GetTime();
    
    for (;;)
    {
        // Wait for messages to arrive
        base::Wait();

        HighPrecisionTime curTime = HighPrecisionTime::GetTime();
        HighPrecisionTime timeDiff = HighPrecisionTime::GetDiff( curTime, oldTime );
        //printf( "Woken up after %ims\n", HighPrecisionTime::ConvertToMilliSeconds( timeDiff ) );
        oldTime = curTime;
        
        base::ProcessMessages();

        ProcessData();
    }
}

//------------------------------------------------------------------------------
void DepthSensorDriver::ProcessData()
{
    bool bAllDataProcessed = false;
    
    while ( !bAllDataProcessed )
    {
        const S32 HEADER_LENGTH = 4;
        const S32 MIN_PACKET_LENGTH = 6;    // U16 PacketID + U16 Byte count + U16 crc
        const S32 MAX_PACKET_LENGTH = 512;
        U8 packetBuffer[ MAX_PACKET_LENGTH ];
        U16 numBytesInPacket = 0;
        bool bPacketReady = false;
        U16 packetID;
        bAllDataProcessed = true;
        
        // First see if there is a packet available to be read from the buffer
        if ( mBuffer.GetNumBytesInBuffer() >= HEADER_LENGTH )
        {   
            // We have at least enough bytes for the packet id and byte count
            U8 byteCountBuffer[ HEADER_LENGTH ];
            mBuffer.PeekAtBytes( byteCountBuffer, HEADER_LENGTH );
            
            packetID = READ_U16( byteCountBuffer );
            numBytesInPacket = READ_U16( &byteCountBuffer[ 2 ] );
            
            if ( DATA_PACKET_ID == packetID )
            {
                if ( mBuffer.GetNumBytesInBuffer() >= numBytesInPacket )
                {
                    assert( numBytesInPacket <= MAX_PACKET_LENGTH && "MAX_PACKET_LENGTH needs to be increased" );
                    mBuffer.ReadBytes( packetBuffer, numBytesInPacket );
                    
                    // Check the packet for errors
                    if ( numBytesInPacket >= MIN_PACKET_LENGTH )
                    {
                        // Get the CRC from the packet
                        U16 packetCRC = READ_U16( &packetBuffer[ numBytesInPacket - 2 ] );
                        
                        if ( CalculateCRC( packetBuffer, numBytesInPacket - 2 ) == packetCRC )
                        {                
                            bPacketReady = true;
                        }
                        else
                        {
                            fprintf( stderr, "Error: Packet with invalid CRC recieved\n" );
                        }
                    }
                    else
                    {
                        fprintf( stderr, "Error: Undersized packet recieved\n" );
                    }
                }
            }
            else
            {
                fprintf( stderr, "Error: Unrecognised packet id recieved\n" );
                // Move forward to the next byte to avoid getting stuck
                mBuffer.AdvanceBuffer( 1 );
                bAllDataProcessed = false;
            }
        }
            
        // Now process any packet which we've received
        if ( bPacketReady )
        {
            assert( DATA_PACKET_ID == packetID );
            
            S32 pressure = READ_S32( &packetBuffer[ 4 ] );
            S32 temperature = READ_S32( &packetBuffer[ 8 ] );
            
            //printf( "Got pressure %i and temperature %i\n", pressure, temperature );
            
            // Publish the data
            player_position1d_data publishData;
            memset( &publishData, 0, sizeof( publishData ) );
            
            publishData.pos = pressure;
            
            base::Publish( this->device_addr, 
                PLAYER_MSGTYPE_DATA, PLAYER_POSITION1D_DATA_STATE, 
                &publishData, sizeof( publishData ) );
            
            // May be something else in the buffer to process
            bAllDataProcessed = false;
        }
    }
}

//------------------------------------------------------------------------------
U16 DepthSensorDriver::CalculateCRC( U8* pData, U32 numBytes )
{
    U32 index = 0;
    U16 crc = 0;

    while( index < numBytes )
    {
        crc = (U8)(crc >> 8) | (crc << 8);
        crc ^= pData[ index++ ];
        crc ^= (U8)(crc & 0xff) >> 4;
        crc ^= (crc << 8) << 4;
        crc ^= ((crc & 0xff) << 4) << 1;
    }
    
    return crc;
}
