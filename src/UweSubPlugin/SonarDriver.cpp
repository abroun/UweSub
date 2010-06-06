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
    pTable->AddDriver( (char*)"SonarDriver", SonarDriverInit );
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
    
    // creating the micron object
    pmicron = new Micron(); // default values constructor (range 20m, resolution 5cms)
    
    
    // initializing serial incoming handling globals
    remainingBytes = 0;
    bufhead = NULL;
    
    // Read options from the configuration file
    RegisterProperty( "buffer_size", &mBufferSize, pConfigFile, section );

    mBuffer.Init( mBufferSize.GetValue() );
    
    // KILL THE ALIVES RIGHT NOW!
    pmicron->sendStopAlives(mpOpaque, this->InQueue);
}

//------------------------------------------------------------------------------
SonarDriver::~SonarDriver()
{
    mBuffer.Deinit();
    // destroy pmicron
    delete pmicron;
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
    if ( Message::MatchMessage(pHeader, PLAYER_MSGTYPE_DATA, PLAYER_OPAQUE_DATA_STATE, mOpaqueID ) )
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
    else if ( Message::MatchMessage(pHeader, PLAYER_MSGTYPE_CMD, PLAYER_SPEECH_CMD_SAY, this->device_addr ) )
    { // Handling message from the client
        player_speech_cmd* pCmd = (player_speech_cmd*)pData;
        
        printf( "Micron command received %s\n", pCmd->string );
        // action
        micron_cmd_t thecmd = micronDecodeCommand(pCmd->string);
        if (thecmd!=micronUNRECOGNIZED) 
          switch(thecmd) {
            case micronREBOOT: // reboot the sonardriver
                    pmicron->sendReboot(mpOpaque, this->InQueue);
                    pmicron->reset();
                    // acknowledge
                    break;
            case micronSET_REGION_FRONT: // select front region for next scan
                    pmicron->setRegion(Micron::frontRegion);
                    // acknowledge
                    break;
            case micronSET_REGION_RIGHT: // select right region for next scan
                    pmicron->setRegion(Micron::rightRegion);
                    // acknowledge
                    break;
            case micronSET_REGION_LEFT: // select left region for next scan
                    pmicron->setRegion(Micron::leftRegion);
                    //acknowledge
                    break;
            case micronSET_REGION_REAR_RIGHT: // select rear right region for next scan
                    pmicron->setRegion(Micron::rearRightRegion);
                    //acknowledge
                    break;
             case micronSET_REGION_REAR_LEFT: // select rear left region for next scan
                    pmicron->setRegion(Micron::rearLeftRegion);
                    //acknowledge
                    break;
             case micronSET_RESOLUTION5: // set resolution to 5cms (bin size)
                    pmicron->setResolution(5);
                    //acknowledge
                    break;
             case micronSET_RESOLUTION10: // set resolution to 10cms (bin size)
                    pmicron->setResolution(10);
                    // acknowledge
                    break;
             case micronSET_RESOLUTION20: // set resolution to 20cms (bin size)
                    pmicron->setResolution(20);
                    // acknowledge
                    break;
             case micronSET_RANGE10: // set range to 10 meters
                    pmicron->setRange(10);
                    // acknowledge
                    break;
             case micronSET_RANGE20: // set range to 20 meters
                    pmicron->setRange(20);
                    //acknowledge
                    break;
             case micronSET_RANGE30: // set range to 30 meters
                    pmicron->setRange(30);
                    // acknlwledge
                    break;
             case micronSCAN_REGION: // scan the selected region
                    pmicron->sendHeadCommand(mpOpaque, this->InQueue, pmicron->currentRegion);
                    // acknowledge
                    break;
        } // end switch
                    
            
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
        // checking for a Data Ready condition
        if (pmicron->getState()==Micron::stDataReady) {
            int i;
            // dumping data
            for (i=0; i<100; i++)
                if (pmicron->regionBins[i]!=NULL) {
                    int len = pmicron->getRange()*100/pmicron->getResolution();
                    int j;
                    for (j=0; j<len; j++)
                        printf("%i  | ",pmicron->regionBins[i][j]);
                    printf("\n");
                }
             pmicron->setState(Micron::stAliveSonar);
        }
                    
            
        // Wait for messages to arrive
        base::Wait();
        
        base::ProcessMessages();
        
        ProcessData();
    }
}

//------------------------------------------------------------------------------
void SonarDriver::ProcessData()
{
    int i;
    // wait a bit
    for (i=0;i<10000; i++);
    U32 numBytesToRead = mBuffer.GetNumBytesInBuffer(); // let's see what we 've got...
  
    if (remainingBytes==0) { // previous packet was fully read
        if ((numBytesToRead==0)&&((pmicron->getState()==Micron::stSendingData)||(pmicron->getState()==Micron::stExpectHeadData))) 
            pmicron->sendHeadCommand(mpOpaque, this->InQueue, pmicron->getRegion()); // no data in queue while scanning, must issue a sendData command
              else if (numBytesToRead>=7) { // nead at least 7 bytes to determine the length of the packet
                        bufhead = (char*)malloc(7); // get the first 7 bytes
                        // reading first 7 bytes in the buffer_size
                        mBuffer.ReadBytes((U8*)bufhead, 7);    
                        remainingBytes = (int)bufhead[5] + (int)bufhead[6] * 256 - 2+1; // get the length of the rest of the message
                    }
    } else if (numBytesToRead>=remainingBytes) { // it's time to get the remaining packet
            int totalbytes = remainingBytes + 7; // calculate total length
            char* buffer = (char*)malloc(totalbytes);
            char* rembuffer = (char*)malloc(remainingBytes);
            // now reading remaining bytes as estimated using the packet header
            // going one-by-one
            for (i=0; i<remainingBytes; i++)
                    mBuffer.ReadBytes((U8*)(&rembuffer[i]), 1);
        
            // tailoring bufhead and rembuffer into buffer
        
            for (i=0; i<totalbytes; i++)
                 if (i<=6) buffer[i] = bufhead[i];
                      else buffer[i] = rembuffer[i-7];
                        // now handling the message
            TritecPacket* pack = Micron::convertBytes2Packet(buffer);
            
            // clearing remaining bytes
            remainingBytes = 0;
            // disposing allocated space
            free(bufhead);
            bufhead = NULL;
            free(rembuffer);
            free(buffer);
            // done
            pmicron->transitionAction(pack);   // change internal state and act
         }
}
