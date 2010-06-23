//------------------------------------------------------------------------------
// File: PingerDriver.cpp
// Desc: A driver to communicate with George's custom sonar hardware
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include <assert.h>
#include "PingerDriver.h"
#include "DataStructures/picmsgs.h"
#include "Common/HighPrecisionTime.h"



// string to message code convertion
pic_cmd_t picDecodeCmd(char* msg) {
    pic_cmd_t code;
    if (strcmp(msg, pic_cmds[picFIRE_TRANSDUCER_0])==0) code = picFIRE_TRANSDUCER_0;
        else if (strcmp(msg, pic_cmds[picFIRE_TRANSDUCER_1])==0) code = picFIRE_TRANSDUCER_1;
            else if (strcmp(msg, pic_cmds[picLISTEN_TRANSDUCER_0])==0) code = picLISTEN_TRANSDUCER_0;
                else if (strcmp(msg, pic_cmds[picLISTEN_TRANSDUCER_1])==0) code = picLISTEN_TRANSDUCER_1;
                    else if (strcmp(msg, pic_cmds[picSEND_ANGULAR_VELOCITY])==0) code = picSEND_ANGULAR_VELOCITY;
                        else if (strcmp(msg, pic_cmds[picSEND_ACCELERATION_X])==0) code = picSEND_ACCELERATION_X;
                            else if (strcmp(msg, pic_cmds[picSEND_ACCELERATION_Y])==0) code = picSEND_ACCELERATION_Y;
                                else code = picCMD_UNKNOWN;
                
    return code;
}


//------------------------------------------------------------------------------
// A factory creation function, declared outside of the class so that it
// can be invoked without any object context (alternatively, you can
// declare it static in the class).  In this function, we create and return
// (as a generic Driver*) a pointer to a new instance of this driver.
Driver* PingerDriverInit( ConfigFile* pConfigFile, int section )
{
    // Create and return a new instance of this driver
    return (Driver*)(new PingerDriver( pConfigFile, section ));
}

//------------------------------------------------------------------------------
// A driver registration function, again declared outside of the class so
// that it can be invoked without object context.  In this function, we add
// the driver into the given driver table, indicating which interfaces the
// driver can support and how to create a driver instance.
void PingerDriverRegister( DriverTable* pTable )
{
    pTable->AddDriver( (char*)"pingerdriver", PingerDriverInit );
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
// PingerDriver
//------------------------------------------------------------------------------
const U32 PingerDriver::DEFAULT_BUFFER_SIZE = 512;
const U16 PingerDriver::DATA_PACKET_ID = 0xEFBE;    // Will appear as 0xBEEF in big-endian

//------------------------------------------------------------------------------
PingerDriver::PingerDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_SPEECH_CODE ),
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
    
     // initializing serial incoming handling globals
    remainingBytes = 0;
    
    state = stIdle;
}

//------------------------------------------------------------------------------
PingerDriver::~PingerDriver()
{
    mBuffer.Deinit();
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int PingerDriver::MainSetup()
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
void PingerDriver::MainQuit()
{
    mpOpaque->Unsubscribe( this->InQueue );
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int PingerDriver::ProcessMessage( QueuePointer& respQueue,
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
            PLAYER_WARN( "Pinger driver buffer is full. Dropping data" );
        }
        return 0;
    }
    else if ( Message::MatchMessage(
        pHeader, PLAYER_MSGTYPE_CMD, PLAYER_SPEECH_CMD_SAY, this->device_addr ) )
    {
        player_speech_cmd_t* pCmd = (player_speech_cmd_t*)pData;
        U8* str;
        
        player_opaque_data_t mData;
        
        printf( "Got %s\n", pCmd->string );
        
        pic_cmd_t thecmd = picDecodeCmd(pCmd->string);
        if (thecmd!=picCMD_UNKNOWN) 
          switch(thecmd) {
            case picFIRE_TRANSDUCER_0: 
                                       mData.data_count = 4;
                                       str = new U8[4];
                                       str[0] = (U8)'F';
                                       str[1] = (U8)'S';
                                       str[2] = (U8)'0';
                                       str[3] = (U8)'\r';
                                       mData.data = str;
       
                                        mpOpaque->PutMsg(this->InQueue, 
                                                          PLAYER_MSGTYPE_CMD, 
                                                          PLAYER_OPAQUE_CMD_DATA, 
                                                           &mData, 0, NULL);
                                       state = stWaitingActiveECho;
                                       delete [] str;
                                       break;
            case picFIRE_TRANSDUCER_1: 
                                       mData.data_count = 4;
                                       str = new U8[4];
                                       str[0] = (U8)'F';
                                       str[1] = (U8)'S';
                                       str[2] = (U8)'1';
                                       str[3] = (U8)'\r';
                                       mData.data = str;
       
                                        mpOpaque->PutMsg(this->InQueue, 
                                                          PLAYER_MSGTYPE_CMD, 
                                                          PLAYER_OPAQUE_CMD_DATA, 
                                                           &mData, 0, NULL);
                                       state = stWaitingActiveECho;
                                       delete [] str;
                                       break;
            case picLISTEN_TRANSDUCER_0: 
                                       mData.data_count = 4;
                                       str = new U8[4];
                                       str[0] = (U8)'L';
                                       str[1] = (U8)'S';
                                       str[2] = (U8)'0';
                                       str[3] = (U8)'\r';
                                       mData.data = str;
       
                                        mpOpaque->PutMsg(this->InQueue, 
                                                          PLAYER_MSGTYPE_CMD, 
                                                          PLAYER_OPAQUE_CMD_DATA, 
                                                           &mData, 0, NULL);
                                       state = stWaitingPassiveEcho;
                                       delete [] str;
                                       break;
            case picLISTEN_TRANSDUCER_1: 
                                       mData.data_count = 4;
                                       str = new U8[4];
                                       str[0] = (U8)'L';
                                       str[1] = (U8)'S';
                                       str[2] = (U8)'1';
                                       str[3] = (U8)'\r';
                                       mData.data = str;
       
                                        mpOpaque->PutMsg(this->InQueue, 
                                                          PLAYER_MSGTYPE_CMD, 
                                                          PLAYER_OPAQUE_CMD_DATA, 
                                                           &mData, 0, NULL);
                                       state = stWaitingPassiveEcho;
                                       delete [] str;
                                       break;
            case picSEND_ANGULAR_VELOCITY: 
                                       mData.data_count = 4;
                                       str = new U8[4];
                                       str[0] = (U8)'A';
                                       str[1] = (U8)'N';
                                       str[2] = (U8)'G';
                                       str[3] = (U8)'\r';
                                       mData.data = str;
       
                                        mpOpaque->PutMsg(this->InQueue, 
                                                          PLAYER_MSGTYPE_CMD, 
                                                          PLAYER_OPAQUE_CMD_DATA, 
                                                           &mData, 0, NULL);
                                       state = stWaitingAngVelocity;
                                       delete [] str;
                                       break;
            case picSEND_ACCELERATION_X: 
                                       mData.data_count = 4;
                                       str = new U8[4];
                                       str[0] = (U8)'A';
                                       str[1] = (U8)'C';
                                       str[2] = (U8)'X';
                                       str[3] = (U8)'\r';
                                       mData.data = str;
       
                                        mpOpaque->PutMsg(this->InQueue, 
                                                          PLAYER_MSGTYPE_CMD, 
                                                          PLAYER_OPAQUE_CMD_DATA, 
                                                           &mData, 0, NULL);
                                       state = stWaitingAcceleration;
                                       delete [] str;
                                       break;
            case picSEND_ACCELERATION_Y: 
                                       mData.data_count = 4;
                                       str = new U8[4];
                                       str[0] = (U8)'A';
                                       str[1] = (U8)'C';
                                       str[2] = (U8)'Y';
                                       str[3] = (U8)'\r';
                                       mData.data = str;
       
                                        mpOpaque->PutMsg(this->InQueue, 
                                                          PLAYER_MSGTYPE_CMD, 
                                                          PLAYER_OPAQUE_CMD_DATA, 
                                                           &mData, 0, NULL);
                                       state = stWaitingAcceleration;
                                       delete [] str;
                                       break;
          }
                
                
        
        return 0;
    }
    
    PLAYER_WARN( "Unhandled message\n" );
    return -1;
}

//------------------------------------------------------------------------------
// Main function for device thread
void PingerDriver::Main()
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
void PingerDriver::ProcessData()
{
   int i;
   U32 numBytesToRead = mBuffer.GetNumBytesInBuffer(); // let's see what we 've got...
 
 
  
  do {
    if (remainingBytes==0) { 
            if (numBytesToRead>=3) { // nead at least 3 bytes to determine the length of the packet
                 // get the first 3 bytes
                 // reading first 3 bytes in bufhead
                 mBuffer.ReadBytes(bufhead, 3); 
                 if (bufhead[0]!=(U8)'*') flushSerialBuffer();
                         else remainingBytes = bufhead[1] + bufhead[2] * 256 -2; // get the length of the rest of the message
                    }
     } else if (numBytesToRead >= remainingBytes) { // it's time to get the remaining packet(s)
            int totalbytes = remainingBytes + 3; // calculate total length
            U8 buffer[totalbytes];
            U8 rembuffer[remainingBytes];
            // now reading remaining bytes as estimated using the packet header
            // going altogether
            mBuffer.ReadBytes(rembuffer, remainingBytes);
        
            // tailoring bufhead and rembuffer into buffer
        
            for (i=0; i<totalbytes; i++)
                 if (i<7) buffer[i] = bufhead[i];
                      else buffer[i] = rembuffer[i-3];
                        // now handling the message
            // handling packet
            PICPacket* pack = PICComm::convertBytes2Packet(buffer);
            
            // clearing remaining bytes
            remainingBytes = 0;
            // done
            PingerDriver::transitionAction(pack);   // change internal state and act
            // disposing the packet
            PICComm::disposePacket(pack);
        }
            
        numBytesToRead = mBuffer.GetNumBytesInBuffer();
        
   } while ((numBytesToRead  >= remainingBytes)&&(remainingBytes>0));
}


// method to change internal state while following incoming data and requests
void PingerDriver::transitionAction(PICPacket* pack) {
    F32 AngularVelocity, AccelerationX, AccelerationY, ObjectDistance;
    U32 PingIntensity;
    U8* EchoData;
    U32 msglen = pack->MsgLen - 3;
    U8 msgtype = pack->MsgType;
    switch(msgtype) {
        case PICComm::msgGyro: // must publish angular velocity value here
                      AngularVelocity = calcAngularVelocity(pack->Message[0]+256*(pack->Message[1]));
                      printf("Angular Velocity: %f\n", AngularVelocity);
                      
                      state = stIdle;
                      break;
        case PICComm::msgAccelerometerX: // must publish acceleration in the X (vertical) axis (positive is DOWN)
                                AccelerationX = calcAcceleration(pack->Message[0]+256*(pack->Message[1]));
                                printf ("Acceleration in X: %f\n", AccelerationX);
                                
                                state = stIdle;
                                break;
        case PICComm::msgAccelerometerY: // must publish acceleration in the Y (horizontal) axis (positive is BACKWARDS)
                                AccelerationY = calcAcceleration(pack->Message[0]+256*(pack->Message[1]));
                                printf("Acceleration in Y: %f\n", AccelerationY);
                                
                                state = stIdle;
                                break;
        case PICComm::msgSonarEcho: if (state==stWaitingActiveECho) {
                                ObjectDistance = locateObstacle(pack->Message);
                                // publish the distance
                                if (ObjectDistance!=-1)
                                    printf("Distance of Object in beam: %f\n", ObjectDistance);
                                else printf("No object in beam");
                            } else if (state==stWaitingPassiveEcho) {
                                PingIntensity = observeEcho(pack->Message);
                                // must publish result
                                
                                printf("Intensity of noise in the transducer: %i", PingIntensity);
                            }
                            state = stIdle;
                            break;
      }
      
                                  
}


// convert analog value to a angular velocity value
F32 PingerDriver::calcAngularVelocity(U32 analog) {
    F32 angvel;
    
    if ((analog >= 345) && (analog <= 351)) angvel = 0;
            else angvel = ((F32)analog - 347.0) * 5 / (1023 * 0.0027);
 return angvel;
}


// convert analog value to  acceleration
F32 PingerDriver::calcAcceleration(U32 analog) {
    F32 acceleration;
    if ((analog >= 542) && (analog <=553 )) acceleration = 0;
            else acceleration = ((F32)analog -544)* 5*10 / (1023*1.040);
    
 return acceleration;
}


F32 PingerDriver::locateObstacle(U8* data) {
    U8 beam[1200];
    U32 i;
    S32 maxcount, maxindex, lowindex, lowcount;
    F32 objectdistance;
    bool counting;
    // clearing out the beam with a threshold - 80 is file
    for (i=0; i<1200; i++)
        beam[i] = (data[i]<80) ? 0 : 100;
    // done
    // Now locating the longest low period
    maxindex = -1;
    lowcount = -1;
    lowindex = -1;
    maxcount = -1;
    counting = false;
    for (i=0; i<1200; i++) {
        if (beam[i]==0) {
            if (counting==false) { // start counting 
                counting = true;
                lowindex = i;
            }
            lowcount++;
        } else {
            if (counting==true) {
                // stop counting
                counting=false;
                if (maxcount<lowcount) {
                    maxcount = lowcount;
                    maxindex = lowindex;
                }
            }
        }
    }
    if (maxindex>-1) objectdistance = 4.5*0.0015*maxindex; // in meters
        else objectdistance = -1;
   
   return objectdistance;
 }

U32 PingerDriver::observeEcho(U8* data) {
    U8 beam[1200];
    U32 i;
    S32 maxcount, maxindex, lowindex, lowcount;
    bool counting;
    // clearing out the beam with a threshold - 80 is file
    for (i=0; i<1200; i++)
        beam[i] = (data[i]<80) ? 0 : 100;
    // done
    // Now locating the longest low period
    maxindex = -1;
    lowcount = -1;
    lowindex = -1;
    maxcount = -1;
    counting = false;
    for (i=0; i<1200; i++) {
        if (beam[i]==0) {
            if (counting==false) { // start counting 
                counting = true;
                lowindex = i;
            }
            lowcount++;
        } else {
            if (counting==true) {
                // stop counting
                counting=false;
                if (maxcount<lowcount) {
                    maxcount = lowcount;
                    maxindex = lowindex;
                }
            }
        }
    }
    
   return maxcount;
 }

        
//------------------------------------------------------------------------------
U16 PingerDriver::CalculateCRC( U8* pData, U32 numBytes )
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

void PingerDriver::flushSerialBuffer()
{
    mBuffer.Clear();
}
