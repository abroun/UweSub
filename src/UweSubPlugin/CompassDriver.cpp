//------------------------------------------------------------------------------
// File: CompassDriver.cpp
// Desc: A driver for controlling a PNI Compass
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include <assert.h>
#include <math.h>
#include "CompassDriver.h"

//------------------------------------------------------------------------------
// A factory creation function, declared outside of the class so that it
// can be invoked without any object context (alternatively, you can
// declare it static in the class).  In this function, we create and return
// (as a generic Driver*) a pointer to a new instance of this driver.
Driver* CompassDriverInit( ConfigFile* pConfigFile, int section )
{
    // Create and return a new instance of this driver
    return (Driver*)(new CompassDriver( pConfigFile, section ));
}

//------------------------------------------------------------------------------
// A driver registration function, again declared outside of the class so
// that it can be invoked without object context.  In this function, we add
// the driver into the given driver table, indicating which interfaces the
// driver can support and how to create a driver instance.
void CompassDriverRegister( DriverTable* pTable )
{
    pTable->AddDriver( (char*)"compassdriver", CompassDriverInit );
}

//------------------------------------------------------------------------------
// Helper routines for reading data types from a buffer. These assume that we're 
// reading big-endian data into little-endian data types
static inline U16 READ_U16( U8* buffer )
{
    return buffer[ 0 ] << 8 | buffer[ 1 ];
}

static inline U32 READ_U32( U8* buffer )
{
    return buffer[ 0 ] << 24 | buffer[ 1 ] << 16 | buffer[ 2 ] << 8 | buffer[ 3 ];
}

static inline F32 READ_F32( U8* buffer )
{
    U32 floatData = READ_U32( buffer );
    return *((F32*)&floatData);
}

//------------------------------------------------------------------------------
// CompassDriver
//------------------------------------------------------------------------------
const U32 CompassDriver::DEFAULT_BUFFER_SIZE = 10000;
const S32 CompassDriver::COMPASS_COMMAND_ID_PACKET_IDX = 2;

//------------------------------------------------------------------------------
// Constructor.  Retrieve options from the configuration file and do any
// pre-Setup() setup.
CompassDriver::CompassDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_IMU_CODE ),
    mBufferSize( "buffer_size", DEFAULT_BUFFER_SIZE, false ),
    mState( eS_Invalid ),
    mExpectedResponse( eCC_None )
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
CompassDriver::~CompassDriver()
{
    mBuffer.Deinit();
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int CompassDriver::MainSetup()
{    
    PLAYER_WARN( "Setting up Compass driver" );

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

    // Start by getting information about the compass
    SendGetModInfoCommand();
    mState = eS_GettingModInfo;

    PLAYER_WARN( "Compass driver ready" );

    return 0;
}

//------------------------------------------------------------------------------
// Shutdown the device
void CompassDriver::MainQuit()
{
    PLAYER_WARN( "Compass driver shutting down");

    mpOpaque->Unsubscribe( this->InQueue );

    PLAYER_WARN( "Compass driver has been shutdown" );
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int CompassDriver::ProcessMessage( QueuePointer& respQueue,
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
            PLAYER_WARN( "Compass driver buffer is full. Dropping data" );
        }
        return 0;
    }
    
    PLAYER_WARN( "Unhandled message\n" );
    return -1;
}

//------------------------------------------------------------------------------
// Main function for device thread
void CompassDriver::Main()
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
void CompassDriver::ProcessData()
{
    const S32 MIN_PACKET_LENGTH = 5;    // U16 Byte count + U8 id + U16 crc
    const S32 MAX_PACKET_LENGTH = 1024;
    U8 packetBuffer[ MAX_PACKET_LENGTH ];
    U16 numBytesInPacket = 0;
    bool bPacketReady = false;
    
    eCompassCommand packetCommand = eCC_None;
    
    // First see if there is a packet available to be read from the buffer
    if ( mBuffer.GetNumBytesInBuffer() >= sizeof( U16 ) )
    {
        // We have at least enough bytes for the byte count
        U8 byteCountBuffer[ sizeof( U16 ) ];
        mBuffer.PeekAtBytes( byteCountBuffer, sizeof( U16 ) );
        numBytesInPacket = READ_U16( byteCountBuffer );
        
        if ( mBuffer.GetNumBytesInBuffer() >= numBytesInPacket )
        {
            assert( numBytesInPacket <= MAX_PACKET_LENGTH && "MAX_PACKET_LENGTH needs to be increased" );
            mBuffer.ReadBytes( packetBuffer, numBytesInPacket );
            
            // Check the packet for errors
            if ( numBytesInPacket >= MIN_PACKET_LENGTH )
            {
                // Get the command id and CRC from the packet
                packetCommand = (eCompassCommand)packetBuffer[ COMPASS_COMMAND_ID_PACKET_IDX ];
                U16 packetCRC = READ_U16( &packetBuffer[ numBytesInPacket - 2 ] );
                
                if ( CalculateCRC( packetBuffer, numBytesInPacket - 2 ) == packetCRC )
                {                
                    bPacketReady = true;
                    if ( eCC_None != mExpectedResponse )
                    {
                        if ( mExpectedResponse == packetCommand )
                        {
                            // We have recieved the response we're waiting for
                            mExpectedResponse = eCC_None;
                        }
                        else
                        {
                            fprintf( stderr, "Error: Unexpected response packet recieved\n" );
                            bPacketReady = false;   // Throw the invalid packet away
                        }
                    }
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
        
    // Now process any packet which we've received
    if ( bPacketReady )
    {
        switch ( mState )
        {
            case eS_GettingModInfo:
            {
                assert( eCC_ModInfoResp == packetCommand );

                U8 typeBuffer[ 5 ];
                memcpy( typeBuffer, &packetBuffer[ 3 ], 4 );
                typeBuffer[ 4 ] = '\0';
                
                U8 revisionBuffer[ 5 ];
                memcpy( revisionBuffer, &packetBuffer[ 7 ], 4 );
                revisionBuffer[ 4 ] = '\0';
                
                printf( "Attached to PNI compass\n" );
                printf( "Compass Type = %s, Revision = %s\n", typeBuffer, revisionBuffer );
                
                SendGetDataCommand();
                mState = eS_PollingForData;
                
                break;
            }
            case eS_PollingForData:
            {
                assert( eCC_DataResp == packetCommand );
                CompassData compassData;
                ExtractDataFromPacket( packetBuffer, numBytesInPacket, &compassData );
                
                // Publish the data
                player_imu_data_euler publishData;
                memset( &publishData, 0, sizeof( player_imu_data_euler ) );
                
                publishData.calib_data.magn_x = compassData.mAlignedMagneticX;
                publishData.calib_data.magn_y = compassData.mAlignedMagneticY;
                publishData.calib_data.magn_z = compassData.mAlignedMagneticZ;
                publishData.orientation.proll = compassData.mRollDegrees*M_PI/180.0f;
                publishData.orientation.ppitch = compassData.mPitchDegrees*M_PI/180.0f;
                publishData.orientation.pyaw = compassData.mHeadingDegrees*M_PI/180.0f;
                
                base::Publish( this->device_addr, 
                    PLAYER_MSGTYPE_DATA, PLAYER_IMU_DATA_EULER, 
                    &publishData, sizeof( publishData ) );
                
                //printf( "H: %2.3f, P: %2.3f, R: %2.3f\n", 
                //    compassData.mHeadingDegrees, compassData.mRollDegrees, compassData.mRollDegrees );
                    
                SendGetDataCommand();
                break;
            }
            default:
            {
                assert( false && "Invalid state encountered" );
            }
        }
    }
}

//------------------------------------------------------------------------------
void CompassDriver::SendGetModInfoCommand()
{
    U8 buffer[] =
    {
        0x00, 0x05,     // Num bytes
        0x01,           // Command id
        0xEF, 0xD4      // CRC
    };
    
    SendCommandDataBuffer( buffer, sizeof( buffer ), eCC_ModInfoResp );
}

//------------------------------------------------------------------------------
void CompassDriver::SendGetDataCommand()
{
    U8 buffer[] =
    {
        0x00, 0x05,     // Num bytes
        0x04,           // Command id
        0xBF, 0x71      // CRC
    };
    
    SendCommandDataBuffer( buffer, sizeof( buffer ), eCC_DataResp );
}

//------------------------------------------------------------------------------
void CompassDriver::SendCommandDataBuffer( void* pData, S32 numBytes, 
                                           eCompassCommand expectedResponse )
{
    assert( eCC_None == mExpectedResponse 
        && "Trying to send a command when we're already waiting for a response" );
    
    player_opaque_data_t dataMsg;
    dataMsg.data_count = numBytes;
    dataMsg.data = (U8*)pData;
    
    mpOpaque->PutMsg( this->InQueue, 
        PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, 
        (U8*)&dataMsg, 0, NULL );
        
    mExpectedResponse = expectedResponse;
}

//------------------------------------------------------------------------------
void CompassDriver::ExtractDataFromPacket( U8* pPacketBuffer, S32 numBytes, 
                                           CompassData* pCompassDataOut )
{
    assert( eCC_DataResp == pPacketBuffer[ COMPASS_COMMAND_ID_PACKET_IDX ] && "Invalid packet type" );
    
    // Clear out the compass data
    memset( pCompassDataOut, 0, sizeof( CompassData ) );
    
    // Look at the payload of the packet (Ignore the byte count, packet id and CRC)
    U8* pDataBuffer = &pPacketBuffer[ COMPASS_COMMAND_ID_PACKET_IDX + 1 ];
    U8* pDataBufferEnd = &pPacketBuffer[ numBytes - 2 ];    
    
    U8 numComponents = *pDataBuffer;
    pDataBuffer++;
    
    while ( pDataBuffer < pDataBufferEnd )
    {
        eCompassDataComponent dataComponent = (eCompassDataComponent)(*pDataBuffer);
        pDataBuffer++;
        switch ( dataComponent )
        {
            case eCDC_HeadingDegrees:
            {
                pCompassDataOut->mHeadingDegrees = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
           case eCDC_TemperatureCelsius:
            {
                pCompassDataOut->mTemperatureCelsius = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_Distortion:
            {
                pCompassDataOut->mbDistortion = (bool)pDataBuffer[ 0 ];
                pDataBuffer++;
                break;
            }
            case eCDC_Calibrated:
            {
                pCompassDataOut->mbCalibrated = (bool)pDataBuffer[ 0 ];
                pDataBuffer++;
                break;
            }    
            case eCDC_PitchCalibratedG:
            {
                pCompassDataOut->mPitchCalibratedG = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_RollCalibratedG:
            {
                pCompassDataOut->mRollCalibratedG = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_IZ_CalibratedG:
            {
                pCompassDataOut->mIZ_CalibratedG = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_PitchDegrees:
            {
                pCompassDataOut->mPitchDegrees = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_RollDegrees:
            {
                pCompassDataOut->mRollDegrees = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_AlignedMagneticX:
            {
                pCompassDataOut->mAlignedMagneticX = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_AlignedMagneticY:
            {
                pCompassDataOut->mAlignedMagneticY = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            case eCDC_AlignedMagneticZ:
            {
                pCompassDataOut->mAlignedMagneticZ = READ_F32( pDataBuffer );
                pDataBuffer += sizeof( F32 );
                break;
            }
            default:
            {
                printf( "Unhandled Data component = %i, idx = %i\n", dataComponent, pDataBuffer - pPacketBuffer );
                assert( false && "Unhandled data component encountered" );
            }
        }
        
        // TODO: It would be nice if this check was done before the read instead of after
        assert( pDataBuffer <= pDataBufferEnd && "Read beyond end of buffer" );
    }
}

//------------------------------------------------------------------------------
U16 CompassDriver::CalculateCRC( U8* pData, U32 numBytes )
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
