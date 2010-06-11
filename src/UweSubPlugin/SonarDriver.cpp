//------------------------------------------------------------------------------
// File: SonarDriver.cpp
// Desc: A driver for controlling a Tritech Micron Sonar
//------------------------------------------------------------------------------
 
//------------------------------------------------------------------------------
#include <stdio.h>
#include <assert.h>
#include <math.h>
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
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_MICRONSONAR_CODE ),
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
    
    // initializing serial incoming handling globals
    remainingBytes = 0;
    
    
    // Read options from the configuration file
    RegisterProperty( "buffer_size", &mBufferSize, pConfigFile, section );

    mBuffer.Init( mBufferSize.GetValue() );
}

//------------------------------------------------------------------------------
SonarDriver::~SonarDriver()
{
    mBuffer.Deinit();
    // destroy pmicron
    
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

    PLAYER_WARN( "Sonar driver ready. Talking to Micron" );
    
    // creating the micron object
    pmicron = new Micron(); // default values constructor (range 20m, resolution 5cms)
    
    // KILL THE ALIVES RIGHT NOW!
    pmicron->sendStopAlives(mpOpaque, this->InQueue);
    
    

    return 0;
}

//------------------------------------------------------------------------------
// Shutdown the device
void SonarDriver::MainQuit()
{
    PLAYER_WARN( "Sonar driver shutting down");

    mpOpaque->Unsubscribe( this->InQueue );
    
    // destroy pmicron
    delete pmicron;
    
    PLAYER_WARN( "Sonar driver has been shutdown" );
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int SonarDriver::ProcessMessage( QueuePointer& respQueue,
                                player_msghdr* pHeader, void* pData )
{   
    
    char micronresp[7];
    
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
    else if ( Message::MatchMessage(pHeader, PLAYER_MSGTYPE_CMD, PLAYER_MICRONSONAR_CMD_SAY, this->device_addr ) )
    { // Handling message from the client
    
        
        player_micronsonar_cmd* pCmd = (player_micronsonar_cmd*)pData;
        
        printf( "Micron command received %s\n", pCmd->string );
        // action
        micron_cmd_t thecmd = micronDecodeCommand(pCmd->string);
        if (thecmd!=micronUNRECOGNIZED) 
          switch(thecmd) {
            case micronREBOOT: // reboot the sonardriver
                   
                    pmicron->sendReboot(mpOpaque, this->InQueue);
                    
                    // must allow a little bit of time (6sec) the sonar to initialize
                    time_t starttime, endtime;
                    time(&starttime);
                    do {
                        time(&endtime);
                    } while (endtime-starttime<6);
                    // most probably sonar 's fine
                    
                    // Now killing the alives
                    pmicron->sendStopAlives(mpOpaque, this->InQueue);
                    
                    // set default values for micron members */
                    pmicron->reset(); 
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    // acknowledge to interested parties
                    /* strcpy(micronresp, micron_msgs[micronALIVE]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
            case micronSET_REGION_FRONT: // select front region for next scan
                    pmicron->setRegion(Micron::frontRegion);
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    // acknowledge
                    /* strcpy(micronresp, micron_msgs[micronREGION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );
                    */
                    break;
            case micronSET_REGION_RIGHT: // select right region for next scan
                    pmicron->setRegion(Micron::rightRegion);
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    // acknowledge
                    /* strcpy(micronresp, micron_msgs[micronREGION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
            case micronSET_REGION_LEFT: // select left region for next scan
                    pmicron->setRegion(Micron::leftRegion);
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    //acknowledge
                     /*strcpy(micronresp, micron_msgs[micronREGION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
            case micronSET_REGION_REAR_RIGHT: // select rear right region for next scan
                    pmicron->setRegion(Micron::rearRightRegion);
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    //acknowledge
                     /*strcpy(micronresp, micron_msgs[micronREGION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSET_REGION_REAR_LEFT: // select rear left region for next scan
                    pmicron->setRegion(Micron::rearLeftRegion);
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    //acknowledge
                    /* strcpy(micronresp, micron_msgs[micronREGION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSET_RESOLUTION5: // set resolution to 5cms (bin size)
                    pmicron->setResolution(5);
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    //acknowledge
                     /*strcpy(micronresp, micron_msgs[micronRESOLUTION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSET_RESOLUTION10: // set resolution to 10cms (bin size)
                    pmicron->setResolution(10);
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    // acknowledge
                    /* strcpy(micronresp, micron_msgs[micronRESOLUTION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSET_RESOLUTION20: // set resolution to 20cms (bin size)
                    pmicron->setResolution(20);
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    // acknowledge
                     /*strcpy(micronresp, micron_msgs[micronRESOLUTION_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSET_RANGE10: // set range to 10 meters
                    pmicron->setRange(10);
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    // acknowledge
                     /*strcpy(micronresp, micron_msgs[micronRANGE_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSET_RANGE20: // set range to 20 meters
                    pmicron->setRange(20);
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    //acknowledge
                     /*strcpy(micronresp, micron_msgs[micronRANGE_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSET_RANGE30: // set range to 30 meters
                    pmicron->setRange(30);
                    
                    // AB: Acknowledge not in interface yet but we can put it in if needed
                    // acknlwledge
                     /*strcpy(micronresp, micron_msgs[micronRANGE_SET]);
                     // sending message to all interested parties (queuepointer = NULL) that data is ready
                     Publish(device_addr,               // device address of this SonarDriver instance
                             PLAYER_MSGTYPE_RESP_ACK,  // Message type is a response to a previous request
                             PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                             (void*)micronresp,        // the string
                              0,                        // deprecated size parameter. Set to 0.
                              NULL,                     // timestamp parameter is NULL. Current time will be used 
                              true                      // copy the data 
                              );*/
                    break;
             case micronSCAN_REGION: // scan the selected region
                    // flushing serial buffer
                    flushSerialBuffer();
                    // clearing any data in the regionBins array
                    pmicron->clearRegionBins();
                    // now sending head command
                    pmicron->sendHeadCommand(mpOpaque, this->InQueue, pmicron->currentRegion);
                    pmicron->sendData(mpOpaque, this->InQueue);
                    
                    // The command is not acknowledged here. If all goes well, a micronDATA_READY
                    // should be published shortly
                    
                    break;
             case micronSTREAM_REGION_DATA: // stream region data available so far
                 int i, j;
                 int linelength = pmicron->getRange()*100/pmicron->getResolution();
                 int linecount=0;
                 // counting region lines 
                 for (i=0; i<Micron::MAX_LINES; i++) 
                     linecount += (pmicron->regionBins[i]!=NULL) ? 1 : 0;
                 // done. now creating a local array to copy the data
                 if (linecount>0) {
                     U8* regionCopy[linelength];
                     // copying the data 
                     for (i=0; i<linecount; i++)
                        for (j=0; j<linelength; j++)  
                             regionCopy[i][j] = pmicron->regionBins[i][j];
                      // region has been copied. Now publishing the data
                      
                      // sending message to all interested parties (queuepointer = NULL) that data is ready
                      Publish(device_addr,               // device address of this SonarDriver instance
                              PLAYER_MSGTYPE_DATA,      // Message type is a response to a previous request
                              PLAYER_MSGTYPE_DATA,      // Message subtype is a data string response (see microncmds.h)
                              (void*)regionCopy,        // the string
                               0,                        // deprecated size parameter. Set to 0.
                               NULL,                     // timestamp parameter is NULL. Current time will be used 
                               true                      // copy the data 
                               );
                       // disposing area data 
                       pmicron->clearRegionBins();
                 }
             
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
        if (pmicron->getState()==Micron::stDataReady) 
        {
            // Publish the latest data as an image. The sonar data is
            // mapped into a quarter circle
            S32 maxPixelRange = pmicron->getRange()*100/pmicron->getResolution();
            
            // Build up the data struct
            player_micronsonar_data_t data;
            data.width = maxPixelRange;
            data.height = maxPixelRange;
            data.bpp = 8;
            data.format = PLAYER_MICRONSONAR_FORMAT_MONO8;
            data.image_count = data.width*data.height;
            data.image = new U8[ data.image_count ];
            memset( data.image, 127, data.image_count );    // Clear image
            
            F32 angleIncrement = (F32)M_PI/(2.0f*(F32)Micron::MAX_LINES);
            
            // Copy the data into the buffer
            // For now determine a pixel by interpolating between the 4 closest readings
            for ( S32 y = 0; y < data.height; y++ )
            {
                S32 invertedY = ( data.height - 1 ) - y;    // Invert y so that we draw from bottom to top
                for ( S32 x = 0; x < data.width; x++ )
                {
                    F32 pixelRange = (F32)sqrt( x*x + invertedY*invertedY );
                    if ( pixelRange > 0.0f && pixelRange < maxPixelRange - 1 )
                    {
                        F32 pixelTheta = atan2( x, invertedY );
                        S32 leftLineIdx = (S32)( pixelTheta / angleIncrement );
                        S32 rightLineIdx = leftLineIdx + 1;
                        if ( leftLineIdx >= 0 && rightLineIdx < Micron::MAX_LINES
                            && NULL != pmicron->regionBins[ leftLineIdx ]
                            && NULL != pmicron->regionBins[ rightLineIdx ] )
                        {
                            // Work out the normalised distance between the 2 lines
                            F32 lineInterp = (pixelTheta - leftLineIdx*angleIncrement)/angleIncrement;
                            
                            // Then work out the normalised distance between the front and back bins
                            S32 nearBinIdx = (S32)pixelRange;
                            S32 farBinIdx = nearBinIdx + 1;
                            F32 binInterp = pixelRange - nearBinIdx;
                            
                            // Fill in the pixel value using bilinear interpolation
                            F32 r1 = pmicron->regionBins[ leftLineIdx ][ nearBinIdx ]*(1.0f - lineInterp)
                                + pmicron->regionBins[ rightLineIdx ][ nearBinIdx ]*lineInterp;
                            F32 r2 = pmicron->regionBins[ leftLineIdx ][ farBinIdx ]*(1.0f - lineInterp)
                                + pmicron->regionBins[ rightLineIdx ][ farBinIdx ]*lineInterp;
                                
                            data.image[ y*maxPixelRange + x ] = 
                                (U8)(r1*(1.0f - binInterp) + r2*binInterp);
                        }
                    }
                }
            }

            // Write data to the client (through the server)
            base::Publish( this->device_addr,
                PLAYER_MSGTYPE_DATA, PLAYER_MICRONSONAR_DATA_STATE, &data );
            delete [] data.image;
            
            // ******************************* dumping data loop. Use for debugging purposes ***************************
            /*int i;
            for (i=0; i<100; i++)
                if (pmicron->regionBins[i]!=NULL) {
                    int len = pmicron->getRange()*100/pmicron->getResolution();
                    int j;
                    for (j=0; j<len; j++)
                        printf("%i  | ",pmicron->regionBins[i][j]);
                    printf("\n");
                }*/
            
            
            // returning to a casual alive state but region data remain allocated until a micronSTREAM_REGION_DATA request
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
    
 U32 numBytesToRead = mBuffer.GetNumBytesInBuffer(); // let's see what we 've got...
 
 
  
  do {
    if (remainingBytes==0) { // previous packet was fully read
       /*if ((numBytesToRead==0)&&(pmicron->getState()==Micron::stSendingData)) 
            pmicron->sendData(mpOpaque, this->InQueue); // no data in queue while scanning, must issue a sendData command
              else */ if (numBytesToRead>=7) { // nead at least 7 bytes to determine the length of the packet
                        // get the first 7 bytes
                        // reading first 7 bytes in bufhead
                        mBuffer.ReadBytes(bufhead, 7); 
                        if (bufhead[0]!=(U8)'@') flushSerialBuffer();
                            else remainingBytes = bufhead[5] + bufhead[6] * 256 - 2+1; // get the length of the rest of the message
                    }
     } else if (numBytesToRead >= remainingBytes) { // it's time to get the remaining packet(s)
            int totalbytes = remainingBytes + 7; // calculate total length
            U8 buffer[totalbytes];
            U8 rembuffer[remainingBytes];
            // now reading remaining bytes as estimated using the packet header
            // going altogether
            mBuffer.ReadBytes(rembuffer, remainingBytes);
        
            // tailoring bufhead and rembuffer into buffer
        
            for (i=0; i<totalbytes; i++)
                 if (i<7) buffer[i] = bufhead[i];
                      else buffer[i] = rembuffer[i-7];
                        // now handling the message
            printf ("Received a package. Will now handle it");
            TritecPacket* pack = Micron::convertBytes2Packet(buffer);
            
            // clearing remaining bytes
            remainingBytes = 0;
            // done
            pmicron->transitionAction(pack, mpOpaque, this->InQueue);   // change internal state and act
            // disposing the packet
            Micron::disposePacket(pack);
        }
            
        numBytesToRead = mBuffer.GetNumBytesInBuffer();
        
} while ((numBytesToRead  >= remainingBytes)&&(remainingBytes>0));
           
         
}


void SonarDriver::flushSerialBuffer()
{
  U32 numBytesToRead;
  if (numBytesToRead = mBuffer.GetNumBytesInBuffer() > 0)  {
  
    U8* dummy = new U8[numBytesToRead];
  
    mBuffer.ReadBytes(dummy, numBytesToRead);
  
    delete [] dummy;
  }
}
