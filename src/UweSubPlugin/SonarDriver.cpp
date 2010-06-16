//------------------------------------------------------------------------------
// File: SonarDriver.cpp
// Desc: A driver for controlling a Tritech Micron Sonar
//------------------------------------------------------------------------------
 
//------------------------------------------------------------------------------
#include <stdio.h>
#include <assert.h>
#include <math.h>
#include "Common/HighPrecisionTime.h"
#include "Common/Utils.h"
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
                    Utils::Sleep( HighPrecisionTime::ConvertFromSeconds( 6.0 ) );
                    // most probably sonar 's fine
                    
                    // Now killing the alives
                    pmicron->sendStopAlives(mpOpaque, this->InQueue);
                    
                    // set default values for micron members */
                    pmicron->reset(); 
                    
                    break;
            case micronSET_REGION_FRONT: // select front region for next scan
                    pmicron->setRegion(Micron::frontRegion);
                    break;
            case micronSET_REGION_RIGHT: // select right region for next scan
                    pmicron->setRegion(Micron::rightRegion);
                    
                    break;
            case micronSET_REGION_LEFT: // select left region for next scan
                    pmicron->setRegion(Micron::leftRegion);
                    
                    break;
            case micronSET_REGION_REAR_RIGHT: // select rear right region for next scan
                    pmicron->setRegion(Micron::rearRightRegion);
                    
                    break;
             case micronSET_REGION_REAR_LEFT: // select rear left region for next scan
                    pmicron->setRegion(Micron::rearLeftRegion);
                    break;
             case micronSET_RESOLUTION5: // set resolution to 5cms (bin size)
                    pmicron->setResolution(5);
                    break;
             case micronSET_RESOLUTION10: // set resolution to 10cms (bin size)
                    pmicron->setResolution(10);
                    break;
             case micronSET_RESOLUTION20: // set resolution to 20cms (bin size)
                    pmicron->setResolution(20);
                    
                    break;
             case micronSET_RANGE10: // set range to 10 meters
                    pmicron->setRange(10);
                    
                    break;
             case micronSET_RANGE20: // set range to 20 meters
                    pmicron->setRange(20);
                    
                    break;
             case micronSET_RANGE30: // set range to 30 meters
                    pmicron->setRange(30);
                    
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
                              (void*)regionCopy,        // copy of bin array 
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
            
            /*U32 dim = 2*pmicron->getRange()*100/pmicron->getResolution()+1;
            data.width = dim;
            data.height = dim;*/
            
            data.width = maxPixelRange;
            data.height = maxPixelRange;
            data.bpp = 8;
            data.format = PLAYER_MICRONSONAR_FORMAT_MONO8;
            data.image_count = data.width*data.height;
            data.image = new U8[ data.image_count ];
            memset( data.image, 127, data.image_count );    // Clear image
            
            /*U32 r, c;
            U32 resol = pmicron->getResolution();
            U32 rang = pmicron->getRange();
            
            U8* tempmatrix[data.width];
            
            for (r=0; r<dim; r++) {
                tempmatrix[r] = new U8[dim];
                for (c=0; c<dim; c++) 
                    tempmatrix[r][c] = 0;
            }
                    
           
            
            SonarDriver::polar2Cartesian(tempmatrix, resol, rang, pmicron->regionBins, 
                             45, 135, rang*100/resol+1, rang*100/resol+1);
                             
            //SonarDriver::mapNormalization(tempmatrix, 2*pmicron->getRange()*100/resol+1, 0.8);
            
           // SonarDriver::mapAutothreshold(tempmatrix, 2*pmicron->getRange()*100/resol+1, 60);
            
            for (r=0; r<data.width; r++) 
                for (c=0; c<data.width; c++)
                    data.image[r*data.width+c] = tempmatrix[r][c];
            
              */  
            
            
            F32 angleIncrement = (F32)M_PI*0.9/180;
            
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
            
            // disposing tempmatrix
            /*for (r=0; r<dim; r++)
                delete [] tempmatrix[r];
            delete [] tempmatrix;*/
            
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


// ********************************* Sonar Image hadnling methods ***********************************

// the following method populates a 2D grid map (1cmx1cm cells) array using a cone of sonar data 
// amap is an array of 1cmx1cm grid cells. Recommended minimum size is 2*arange*100+1
// specify startangle and endangle in degrees in counter-clockwise fashion
// arange in meters, aresolution in centimeters
// (ipos, jpos) is the position of the micron in amap. recommended (arange*100, arange*100).
void SonarDriver::polar2Cartesian(U8** amap, U32 aresolution, U32 arange, U8** abins, 
                             U32 startangle, U32 endangle, U32 ipos, U32 jpos)  {
    
    // retrieving dimension of the map (each bin is a pixel)
    U32 dim = 2*arange*100/aresolution+1;
    F32 theta;
    U32 r, c;
    U32 rows = (endangle-startangle)*10/9; // rows of the abins array (lines are 0.9 degrees apart)
    U32 cols = arange*100/aresolution; // length of the line in cms
    // must start from the ending angle since the micron scans from left to right
    for (r = 0; r< rows; r++) {
        // ontaining the corresponding angle in rads
        theta = ((F32)endangle - r*0.9)*M_PI/180;
        for (c=0; c<cols; c++) {
            // computing bin coordinates of the point on which diagonals cross (bin is a rectangle)
            F32 binCX = (F32)(c*1.0)*cos(theta);
            F32 binCY = (F32)(c*1.0)*sin(theta);
            // now finding the dimensions of the bin for the given position
            
            // F32 binWidth = (F32)abs((1.0*aresolution)*cos(theta));
            // F32 binHeight = (F32)abs((1.0*aresolution)*sin(theta));
            // now computing the coordinates of the bin in the map array, 
            // given that micron is "sitting" at (ipos, jpos)
            // U32 bini = ipos + (U32)(binCY - binHeight/2.0);
            // U32 binj = jpos + (U32)(binCX - binWidth/2.0);
            U32 bini = ipos +(U32)binCY;
            U32 binj = jpos + (U32)binCX;
            // now filling the rectangular area. obviously there will be certain overlappings but it is ok
            // U32 bw_int= (U32)binWidth;
            // U32 bh_int = (U32)binHeight;
            amap[bini][binj] = abins[r][c];
            /*
            int k, l;
            for (k=-(bh_int/2); (S32)k<=(S32)(bh_int/2); k++) 
            {   
                for (l=-(bw_int/2); (S32)l<=(S32)(bw_int/2); l++) {
                    if ((bini+k>0)&&(bini+k<2*arange*100/aresolution+1)&&
                        (binj+l>0) && (binj+l<2*arange*100/aresolution+1)) amap[bini+k][binj+l] = abins[r][c];
                }
            }
            */
        }
        // Rectangular grid map updated
    } 
}

// Map Normalization. This method normalizes the entire map by convolving with the 2D normal distribution
// sigma is the square root of standard deviation or diaspora. A value of 2 will suffice
void SonarDriver::mapNormalization(U8* amap[], U32 dim, F32 sigma) {
    
    F32 Kernel[5][5]; // Gaussian Kernel matrix 5x5
    int i, j, r, c, rows=dim, cols=dim, resultcols, resultrows;
    
    F32 sum;
    // initializing convolution kernel
    for (i=-2; i<=2; i++)
        for (j=-2; j<=2; j++) 
            Kernel[i+2][j+2] = exp(-(i*i+j*j)/(2*sigma*sigma))/(2*M_PI*sigma*sigma);
    // done
    
    // computing dimensions of the resulting array following a convolution
    resultcols = cols; // normally the dimmension is N-m+1... Here we demand convolution result to be of same dimension
    resultrows = rows; // convoluted image rows
    // allocating space for the result image array 
    U8 result[resultrows][resultcols];
    // ************ main loop ***************
    for (r=0; r<resultrows; r++) 
        for (c=0; c<resultcols; c++) {
            sum =0;
            // convolving
            for (i=0; i<5; i++)
                for (j=0; j<5; j++) 
                    if ((r+i > 0)&&(c+j>0)&&(r+i<rows)&&(c+j<cols)) // index inside the array
                        sum += Kernel[i][j]*amap[r+i][c+j];
             // convolution result stored in sum now.
            result[r][c] = (U8)sum;
        }
    //**********  main loop ends ***************
    
    // now updating the map
    for (r=0; r<rows; r++)
        for (c=0; c<cols; c++) 
             amap[r][c] = result[r][c];
    

}

// Threshold the array. I believe a good threshold whould be close to 100. Only experiments will show though...
// Unfortunately, autothreshold will not work since it will depend on the environment around the robot.
// if, for example, the environment is relatively clear, the autothreshold will produce misinterpretations
// by assigning a 255 value to low noise findings.
void SonarDriver::mapAutothreshold(U8* amap[], U32 dim, U8 threshold) {
    U32 i, j;
    
    
    
     // now thresholding...
     for (i=0; i<dim; i++)
         for (j=0; j<dim; j++)
             amap[i][j] = (amap[i][j] < threshold) ? 0 : 255;
     // done
     
     
}