
#include "Micron.h"


 
// Tritec Protocol Command Constants
 const U8 Micron::mtVersionData = 1; // Version reply by the micron
 const U8 Micron::mtHeadData = 2; // Head data reply by the micron
 const U8 Micron::mtAlive = 4;    // Alive reply by the micron
 const U8 Micron::mtBBUserData = 6; // User data reply by the micron
 const U8 Micron::mtReBoot = 16; // Reboot sonar
 const U8 Micron::mtHeadCommand = 19; // configure the micron for scanning
 const U8 Micron::mtSendVersion = 23;  // request parameters from micron
 const U8 Micron::mtSendBBUser = 24; // request user data from micron
 const U8 Micron::mtSendData = 25;   // request half/full duplex data from micron
 const U8 Micron::mtStopAlive = 0x42; // forces micron to stop sedning repeated alive msgs
        
// Commands ends 

// alive constants
 const U8 Micron::alFalseAlive = 0;
 const U8 Micron::alNoParams=1;
 const U8 Micron::alParamsAck = 2;
 const U8 Micron::alInScan = 3;



// state constants
 const int Micron::stIdle = 0;
 const int Micron::stConnected = 1;
 const int Micron::stExpectAlive = 2;
 const int Micron::stAliveSonar = 3;
 const int Micron::stExpectHeadAlive = 4;
 const int Micron::stSendingData = 5;
 const int Micron::stExpectHeadData = 6;
 const int Micron::stExpectUserData = 7;
 const int Micron::stDataReady = 8;
 
const F32 Micron::DEFAULT_GAIN = 0.1f;
const S32 Micron::MIN_RANGE = 2;
const S32 Micron::MAX_RANGE = 100;
const S32 Micron::MIN_AD_INTERVAL = 5;  // In units of 640ns

void Micron::ScanData::clear()
{
    for ( S32 rayIdx = 0; rayIdx < MAX_NUM_RAYS; rayIdx++ )
    {
        mRays[ rayIdx ].mNumBins = 0;
    }
    mNumRaysScanned = 0;
}

// parametric constructor
Micron::Micron(int range, int resolution, int ADlow, int ADspan) {
            
    setRangeAndResolution( range, resolution );
    Micron::mADlow = ADlow;
    Micron::mADspan = ADspan;
    setGain( DEFAULT_GAIN );
    
    // setting state and selected region to scan
    state = stIdle;
    setRegion( eR_Full );
}

// default values constructor
Micron::Micron() {
    setRangeAndResolution( 20, 5 ); // 20 m standard range and 5 cm standard resolution
    Micron::mADlow = 40;     // 40 dB standard AD low limit
    Micron::mADspan = 24;    // 24 dB  standard AD span
    setGain( DEFAULT_GAIN );
   
    state = stAliveSonar; // starting from alive state. Assumming Sonar connected and powered
    setRegion( eR_Full );
}


Micron::~Micron() {
}


// reset (call after a reboot)
void Micron::reset() {
    // Clear out scan data
    mScanData.clear();
    
    // setting current region to frontRegion
    setRegion( eR_Front );

    // setting state
    state = stConnected;
}

// This function should kill constant alive messages from the micron
void Micron::sendStopAlives(Device* theOpaque, QueuePointer inqueue) {
       TritecPacket* salpack = makeStopAlives();
       // retrieving the length
       int len = packetLength(salpack);
       // converting to raw data_count
       U8* salraw = convertPacket2Bytes(salpack);
       // sending the packet
       player_opaque_data_t mData;
       mData.data_count = len;
       mData.data = salraw;
       
       
       theOpaque->PutMsg(inqueue, PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, &mData, 0, NULL); 
        // Data sent
        // Now disposing packet and raw data
        disposePacket(salpack);
        delete [] salraw;
        // changing state
        state = stAliveSonar; // Sonar should be alive
}

//this function sends a reboot command to the micron
void Micron::sendReboot(Device* theOpaque, QueuePointer inqueue) {
       TritecPacket* rbpack = makeReboot();
        // retrieving the length
        int len = packetLength(rbpack);
        // converting to raw data
        U8* rbraw = convertPacket2Bytes(rbpack);
        // sending the data
        player_opaque_data_t mData;
        mData.data_count = len;
        mData.data = rbraw;

        theOpaque->PutMsg( inqueue,  PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, &mData, 0, NULL); 
        // Data sent
        // Now disposing packet and raw data
        disposePacket(rbpack);
        delete [] rbraw;
        // changing state
         state = stExpectAlive; // waiting for an alive answer
}


// this method sends a BBUSerCommand. Not needed, using old firmware
void Micron::sendBBUser(Device* theOpaque, QueuePointer inqueue) {
        TritecPacket* bbpack = makeSendBBUser();
         // retrieving length 
         int len = packetLength(bbpack);
         // converting to raw data
         U8* rawbb = convertPacket2Bytes(bbpack);
         // send the data
         player_opaque_data_t mData;
         mData.data_count = len;
         mData.data = (uint8_t*)rawbb;

        theOpaque->PutMsg( inqueue,  PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, &mData, 0, NULL);
        // Data sent
        // disposing packet and raw data 
        disposePacket(bbpack);
        delete [] rawbb;
        // changing state
        state = stExpectUserData;
}


// this function sends an mtSendVersion command
void Micron::sendVersion(Device* theOpaque, QueuePointer inqueue) {
       // creating a sendVersion packet
       TritecPacket* svpack = makeSendVersion();
       // retrieving the length
       int len = packetLength(svpack);
       // converting to raw data
       U8* svraw = convertPacket2Bytes(svpack);
       // send the data
       player_opaque_data_t mData;
       mData.data_count = len;
       mData.data = (uint8_t*)svraw;

       theOpaque->PutMsg( inqueue,  PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, &mData, 0, NULL);
       // data sent
       // disposing the packet and raw data
       disposePacket(svpack);
       delete [] svraw;
       // changing state
       state = stExpectAlive; // waiting for an alive answer
}

// this function sends an mtHeadCommand
void Micron::sendHeadCommand(Device* theOpaque, QueuePointer inqueue) 
{
    mScanData.clear();
    
    // creating the head packet
    TritecPacket* headpack = makeHead( mRange, mNumBins, 
        mStartAngle, mEndAngle, mADlow, mADspan, mGain, &mScanData.mSettings );
  
    // retrieving length
    int len = packetLength(headpack);
    // converting to raw data
    U8* headraw = convertPacket2Bytes(headpack);
    
    // sending Command
    player_opaque_data_t mData;
    mData.data_count = len;
    mData.data = (uint8_t*)headraw;

    theOpaque->PutMsg( inqueue,  PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, &mData, 0, NULL);
    // data sent
    // disposing the packet and raw data
    disposePacket(headpack);
    delete [] headraw;
    // changing state
       
    state = stSendingData; // it should be stExpectHeadAlive but nobody knows....
}

// this functions sens a sendData command
void Micron::sendData(Device* theOpaque, QueuePointer inqueue) {
            // creating a sendData command packet
            TritecPacket* sdpack = makeSendData();
            //retrieving length
            int len = packetLength(sdpack);
            // converting to raw data
            U8* sdraw = convertPacket2Bytes(sdpack);
            // sending packet
            player_opaque_data_t mData;
            mData.data_count = len;
            mData.data = sdraw;

            theOpaque->PutMsg( inqueue,  PLAYER_MSGTYPE_CMD, PLAYER_OPAQUE_CMD_DATA, &mData, 0, NULL);
            // data sent
            // disposing packet and raw data
            disposePacket(sdpack);
            delete [] sdraw;
            // changing state
            state = stExpectHeadData; // waiting for head data to arrive
        }

// this functions changes state according to the response from the sonar
void Micron::transitionAction(TritecPacket* pack, Device* theOpaque, QueuePointer inqueue) {
        U8 cmd = pack->Msg[0]; // get command

        int datalen=0, transducerAngle=0;
        U8* linebins = NULL;
        //for (int d =0; d<10000; d++);
        
        switch(cmd) {
          case mtBBUserData: // received an answer to a sendBBUserCommand
             switch(state) {
               case stExpectUserData:
                             state = stAliveSonar;
                             break;
               case stConnected:
                             state = stAliveSonar; // must be alive
                             break;
               case stExpectHeadData: // do nothing, although it shouldn't happen
                             break;
               case stIdle:
                            state = stAliveSonar; // must be alive
                            break;
               case stAliveSonar: 
                            state = stAliveSonar; // must be alive
                            break;
               case stDataReady: // nothing
                            break;
               }
               break;
          case mtVersionData: // received an mtVersion  packet
                    switch (state)
                    {
                    case stExpectAlive: // waiting on an alive by a sendversion
                                state = stAliveSonar;
                            break;
                    case stConnected: // connected and may get an automatic alive
                                sendStopAlives(theOpaque, inqueue); // killing alives just in case
                                state = stAliveSonar;
                            break;
                    case stExpectHeadAlive: // waiting on an alive response to a head command (unlikely to happen)
                                state = stSendingData; // we are now clear to request data
                            break;
                    case stIdle: // haven't done anything, but the micron may be sending constant alives or versions
                            // the sonar is alive and send constant alives. Killing alives...
                            sendStopAlives(theOpaque, inqueue); // stop the alives anyway
                            break;
                    case stDataReady: // nothing
                            break;
                    }
                    break;
           case mtAlive: // received an alive packet
                    switch(state) {
                        case stExpectAlive: // waiting on an alive by a sendversion
                            if (validateAlive(pack)!=alFalseAlive) state = stAliveSonar;
                                else sendStopAlives(theOpaque, inqueue); // kill alives anyway (to be sure)
                            break;
                        case stConnected: // connected and may get an automatic alive
                                sendStopAlives(theOpaque, inqueue); // stopping alives
                                // clear incoming buffer
                            break;
                        case stExpectHeadAlive: // waiting on an alive response to a head command
                            // if (validateAlive(pack)==alParamsAck) state = stExpectHeadData;
                            state = stSendingData; // clear to request data lines now
                            // ********* clear incoming buffer
                            break;
                        case stSendingData: // in case an alive comes after a head command
                            // clear the incoming buffer or do nothing
                            break;
                        case stAliveSonar: // it's alive but we are getting alives.
                            sendStopAlives(theOpaque, inqueue); // kill the alives
                            break;
                        case stDataReady: 
                            // killing alives
                            sendStopAlives(theOpaque, inqueue);
                            state = stDataReady;
                            break;
                    }
                    break;
                
            case mtHeadData:
                    switch(state) {
                        case stConnected: // nothing.
                            break;
                        case stExpectAlive: // nothing
                            break;
                        case stExpectHeadAlive: // nothing
                            break;
                        case stExpectHeadData: 
                        case stSendingData:
                        {                               
                            linebins = unwrapHeadData(pack, &datalen, &transducerAngle);
                            S32 angleDiffToRay = transducerAngle - mScanData.mSettings.mStartAngle;
                            while ( angleDiffToRay < 0 )
                            {
                                angleDiffToRay += MAX_SONAR_ANGLE;
                            }
                            assert( angleDiffToRay >= 0 
                                && angleDiffToRay <= mScanData.mSettings.GetAngleDiff() && "Unexpected angle diff" );
                            S32 rayIdx = (angleDiffToRay / SONAR_STEP_ANGLE);
                            assert( rayIdx*SONAR_STEP_ANGLE == angleDiffToRay && "Step size error" );
                            
                            memcpy( mScanData.mRays[ rayIdx ].mBins, linebins, datalen );
                            mScanData.mRays[ rayIdx ].mNumBins = datalen;
                            mScanData.mNumRaysScanned++;
                            
                            // TODO: Find a slightly less flaky way to signal the end of a scan
                            S32 mNumRaysPerScan = mScanData.mSettings.GetAngleDiff()/SONAR_STEP_ANGLE;
                            printf( "Num rays to scan = %i Got ray %i\n", mNumRaysPerScan, rayIdx );
                            if ( mScanData.mNumRaysScanned > 0
                                && (mScanData.mNumRaysScanned % mNumRaysPerScan) == 0 )
                            {
                                printf( "Finished\n" );
                                state = stDataReady;
                            }
                            else
                            {
                                if ( rayIdx % 2 == 1 )
                                {
                                    printf( "Sending next package\n" );
                                    Micron::sendData(theOpaque, inqueue);
                                }
                                state = stExpectHeadData;
                            }
            
                            break;
                        }
                        case stIdle: //nothing
                            break;
                        case stDataReady: // nothing... it shouldn't happen
                            break;
                    }
                    break;
                
            }
}


        

int Micron::packetLength(TritecPacket* tp) {
     int binlength = tp->MsgLength[0] + (tp->MsgLength[1])*256;
     return 5 + binlength + 1; // first 5 bytes + messagelength+line feed
}

U8* Micron::convertPacket2Bytes(TritecPacket* tp) {
            int rawlen = packetLength(tp);
            U8* rawmsg = new U8[rawlen];
            // now filling the raw bytes array
            rawmsg[0] = tp->Header;
            // hex length
            rawmsg[1] = tp->HexMsgLength[0];
            rawmsg[2] = tp->HexMsgLength[1];
            rawmsg[3] = tp->HexMsgLength[2];
            rawmsg[4] = tp->HexMsgLength[3];
            // hex length copied
            // bin length
            rawmsg[5] = tp->MsgLength[0];
            rawmsg[6] = tp->MsgLength[1];
            // bin length copied
            rawmsg[7] = tp->TxNdeID;
            rawmsg[8] = tp->RxNdeID;
            rawmsg[9] = tp->MsgBytes;
            int i;
            // now copying the message
            for (i = 0; i < tp->MsgBytes ; i++)
                rawmsg[10 + i] = tp->Msg[i];
            // message copied
            // adding a line feed terminator
            rawmsg[rawlen - 1] = 0x0A;
            // packet converted

            return rawmsg;
}


// packet disposal
void Micron::disposePacket(TritecPacket* pack) {
    // disposing the hex length string
    delete [] pack->HexMsgLength;
    // disposing the length bytes
    delete [] pack->MsgLength;
    // disposing the messagelength
    delete [] pack->Msg;
    // now disposing the packet
    delete  pack;
}

        
TritecPacket* Micron::makeSendBBUser() {
       
    TritecPacket* bbpack = new TritecPacket();
    
    bbpack->Header = (U8)'@';
    bbpack->HexMsgLength = new U8[4];
    bbpack->HexMsgLength[0] = 0x30;
    bbpack->HexMsgLength[1] = 0x30;
    bbpack->HexMsgLength[2] = 0x30;
    bbpack->HexMsgLength[3] = 0x38;
    bbpack->MsgLength = new U8[2];
    bbpack->MsgLength[0] = 8;
    bbpack->MsgLength[1] = 0;
    bbpack->TxNdeID = 255;
    bbpack->RxNdeID = 2;
    bbpack->MsgBytes = 3;
    bbpack->Msg = new U8[3];
    bbpack->Msg[0] = mtSendBBUser;
    bbpack->Msg[1] = 0x80;
    bbpack->Msg[2] = 2;
    bbpack->Terminator = 0x0A;

    return bbpack;
}


TritecPacket* Micron::makeReboot() {
     TritecPacket* rbpack = new TritecPacket();
     
     rbpack->Header = (U8)'@';
     rbpack->HexMsgLength = new U8[4];
     rbpack->HexMsgLength[0] = (U8)'0';
     rbpack->HexMsgLength[1] = (U8)'0';
     rbpack->HexMsgLength[2] = (U8)'0';
     rbpack->HexMsgLength[3] = (U8)'8';
     rbpack->MsgLength = new U8[2];
     rbpack->MsgLength[0] = 8;
     rbpack->MsgLength[1] = 0;
     rbpack->TxNdeID = 255;
     rbpack->RxNdeID = 2;
     rbpack->MsgBytes = 3;
     rbpack->Msg = new U8[3];
     rbpack->Msg[0] = mtReBoot;
     rbpack->Msg[1] = 0x80;
     rbpack->Msg[2] = 2;
     rbpack->Terminator = 0x0A;

     return rbpack;
}

TritecPacket* Micron::makeSendVersion() {
      TritecPacket* sverpack = new TritecPacket();
       
      sverpack->Header = (U8)'@';
      sverpack->HexMsgLength = new U8[4];
      sverpack->HexMsgLength[0] = (U8)'0';
      sverpack->HexMsgLength[1] = (U8)'0';
      sverpack->HexMsgLength[2] = (U8)'0';
      sverpack->HexMsgLength[3] = (U8)'8';
      sverpack->MsgLength = new U8[2];
      sverpack->MsgLength[0] = 8;
      sverpack->MsgLength[1] = 0;
      sverpack->TxNdeID = 255; // pc is transmitter
      sverpack->RxNdeID = 2;   // micron is the receiver
      sverpack->MsgBytes = 3;   // 3 bytes message payload
      sverpack->Msg = new U8[3];
      sverpack->Msg[0] = mtSendVersion;
      sverpack->Msg[1] = 0x80;
      sverpack->Msg[2] = 2;
      sverpack->Terminator = 0x0A; // put a line feed at the end

      return sverpack;
}


TritecPacket* Micron::makeStopAlives() {
      
      TritecPacket* salpack = new TritecPacket();

      salpack->Header = (U8)'@';
      salpack->HexMsgLength = new U8[4];
      salpack->HexMsgLength[0] = 0x30;
      salpack->HexMsgLength[1] = 0x30;
      salpack->HexMsgLength[2] = 0x30;
      salpack->HexMsgLength[3] = 0x38;
      salpack->MsgLength = new U8[2];
      salpack->MsgLength[0] = 8;
      salpack->MsgLength[1] = 0;
      salpack->TxNdeID = 255;
      salpack->RxNdeID = 2;
      salpack->MsgBytes = 3;
      salpack->Msg = new U8[3];
      salpack->Msg[0] = mtStopAlive;
      salpack->Msg[1] = 0x80;
      salpack->Msg[2] = 2;
      salpack->Terminator = 0x0A;

      return salpack;
}



U8* Micron::unwrapHeadData(TritecPacket* hdatapack, int* pDataLenOut, int* pTransducerAngleOut ) {
      
    *pDataLenOut = hdatapack->Msg[32] + 256 * hdatapack->Msg[33];
    *pTransducerAngleOut = hdatapack->Msg[30] + 256 * hdatapack->Msg[31];
    
    return &hdatapack->Msg[34];
}


TritecPacket* Micron::makeSendData() {
            
   TritecPacket* sdatapack = new TritecPacket();
    
   sdatapack->Header = (U8)'@';
   sdatapack->HexMsgLength = new U8[4];
   sdatapack->HexMsgLength[0] = 0x30;
   sdatapack->HexMsgLength[1] = 0x30;
   sdatapack->HexMsgLength[2] = 0x30;
   sdatapack->HexMsgLength[3] = 0x43;
   sdatapack->MsgLength = new U8[2];
   sdatapack->MsgLength[0] = 0x0C;
   sdatapack->MsgLength[1] = 0x00;
   sdatapack->TxNdeID = 255;
   sdatapack->RxNdeID = 2;
   sdatapack->MsgBytes = 7;
   sdatapack->Msg = new U8[7];
   sdatapack->Msg[0] = mtSendData;
   sdatapack->Msg[1] = 0x80;
   sdatapack->Msg[2] = 2;
   sdatapack->Msg[3] = 0; // no time synchronization. 
   sdatapack->Msg[4] = 0; // sending zeros in the time fields
   sdatapack->Msg[5] = 0; // time field 3
   sdatapack->Msg[6] = 0; // time field 4
   sdatapack->Terminator = 0x0A;

   return sdatapack;
}


int Micron::validateAlive(TritecPacket* alivepack) {
    
  int status;
  U8 headinfo;
  if (packetLength(alivepack) != 22) status = alFalseAlive;
    else {
           headinfo = alivepack->Msg[10]; // retrieving HeadInfo
           int inscan = (headinfo >> 5) & 0x1;
           int noparams = (headinfo >> 6) & 0x1;
           int sentcfg = (headinfo >> 7) & 0x1;
           if (inscan == 1) status = alInScan;
              else if (sentcfg == 1) status = alParamsAck;
                else if (noparams == 1) status = alNoParams;
                   else status = alFalseAlive;
            }
   return status;
}


// specify resolution in cms, range in meters
TritecPacket* Micron::makeHead( int range, int numBins, 
                                int startAngle, int endAngle,
                                int ADlow, int ADspan, F32 gain, ScanSettings* pScanSettingsOut )
{
    ScanSettings scanSettings;
    
  TritecPacket* headpack = new TritecPacket();
  headpack->Header = (U8)'@';
  headpack->HexMsgLength = new U8[4];
  headpack->HexMsgLength[0] = 0x30; //0
  headpack->HexMsgLength[1] = 0x30; //0
  headpack->HexMsgLength[2] = 0x34;
  headpack->HexMsgLength[3] = 0x43;

  headpack->MsgLength = new U8[2];
  headpack->MsgLength[0] = 76; //76 bytes
  headpack->MsgLength[1] = 0;
  headpack->TxNdeID = 255; //pc 
  headpack->RxNdeID = 2; //  micron id
  headpack->MsgBytes = 71; // 55 bytes left
  // creating the message array
  headpack->Msg = new U8[71];
  // now filling the message array
  headpack->Msg[0] = mtHeadCommand; // command id
  headpack->Msg[1] = 0x80;
  headpack->Msg[2] = 2;
  headpack->Msg[3] = 0x1D; // NOT including channel params 
  // configuring Head Control now
  // low byte
  headpack->Msg[4] = 0x85;
  // bit 0:     1  ADC 8-bit
  // bit 1:     0  Sector Scan
  // bit 2:     1  for right scan, 0 for left scan (here set 1 orginally for masking)
  // bit 3:     0  ignored when doing sector scan
  // bit 4:     0  motor enabled (makes no difference in the micron)
  // bit 5:     0  sonar transmitter enabled
  // bit 6:     0  always
  // bit 7:     1  low Frequency channel

  // high byte
  headpack->Msg[5] = 0x23;
  // bit 0:     1 always 
  // bit 1:     1 for the micron
  // bit 2:     0 no heading offsets
  // bit 3:     0 no sidescan
  // bit 4:     0 (ignored by micron)
  // bit 5:     1 Analog Scan Line data reply
  // bit 6:     0 must be zero
  // bit 7:     0 must be zero unless sensor fails
  // done with head control configuration
  headpack->Msg[6] = 3; // headtype is DST
  headpack->Msg[7] = 0x99; //ignored by micron (DST)
  headpack->Msg[8] = 0x99; //ignored by micron (DST)-included so that i dont lose track
  headpack->Msg[9] = 0x99; // ignored by micron
  headpack->Msg[10] = 0x02; // ignored
  headpack->Msg[11] = 0x66; // ignored by micron (DST)
  headpack->Msg[12] = 0x66; // ignored by micron (DST)
  headpack->Msg[13] = 0x66; // ignored by micron (DST)
  headpack->Msg[14] = 0x5; // ignored by micron (DST)
  headpack->Msg[15] = 0xA3; // ignored by micron (DST)
  headpack->Msg[16] = 0x70; // ignored by micron (DST)
  headpack->Msg[17] = 0x3D; // ignored by micron (DST)
  headpack->Msg[18] = 0x06; // ignored by micron
  headpack->Msg[19] = 0x70; // ignored by micron (DST)
  headpack->Msg[20] = 0x3D; // ignored by micron (DST)
  headpack->Msg[21] = 0x0A; // ignored by micron (DST)
  headpack->Msg[22] = 0x09; // ignored by micron (DST)
  headpack->Msg[23] = 0x28; // ignored by micron (DST)
  headpack->Msg[24] = 0x00; // ignored by micron (DST)
  // setting up the range
  int drange = range * 10;
  headpack->Msg[25] = (U8)(drange & 0xFF); // range in decimeters, low byte
  headpack->Msg[26] = (U8)((drange >> 8) & 0xFF); // range in dm, high byte
  
  scanSettings.mStartAngle = startAngle;
  scanSettings.mEndAngle = endAngle;
      
   headpack->Msg[27] = (U8)(startAngle & 0xFF);
   headpack->Msg[28] = (U8)((startAngle >> 8) & 0xFF);
   headpack->Msg[29] = (U8)(endAngle & 0xFF);
   headpack->Msg[30] = (U8)((endAngle >> 8) & 0xFF);

   // calculating AdLow and AdSpan
   headpack->Msg[31] = (U8)(ADspan * 255 / 80); // AD span in range 0-255
   headpack->Msg[32] = (U8)(ADlow * 255 / 80); // AD low in range 0-255

   const U8 MAX_GAIN = 210;
   U8 gainByte = (U8)(gain * MAX_GAIN);
   
   headpack->Msg[33] = gainByte; // initial gain for channel #1
   headpack->Msg[34] = gainByte; // initial gain for channel #2

   headpack->Msg[35] = 0x5A; // channel 1 slope low char, ignored
   headpack->Msg[36] = 0x00; // channel 1 slope high char, ignored

   headpack->Msg[37] = 0x7D; // channel 2 slope low byte, ignored
   headpack->Msg[38] = 0x00; // channel 2 slope high byte, ignored

   headpack->Msg[39] = 0x20; // 3.2 usec motor step time
   headpack->Msg[40] = SONAR_STEP_ANGLE; // In 1/16 Grads
   
   scanSettings.mStepAngle = SONAR_STEP_ANGLE;

   scanSettings.mRange = range;
   scanSettings.mNumBins = numBins;
   
   
   // ******** now caculating AD interval and Number of Bins **************
   S32 ADInterval = calculateADInterval( range, numBins );
   
   if ( ADInterval < MIN_AD_INTERVAL )
   {
       fprintf( stderr, "Error: Unable to make AD interval small enough\n" );
       ADInterval = MIN_AD_INTERVAL;
   }

   headpack->Msg[41] = (U8)(ADInterval & 0xFF); // AD interval low byte. 
   headpack->Msg[42] = (U8)((ADInterval >> 8) & 0xFF);  // AD interval high byte

   headpack->Msg[43] = (U8)(numBins & 0xFF); // Number of Bins Low byte
   headpack->Msg[44] = (U8)((numBins >> 8) & 0xFF); // Number of Bins high byte

    // **************** done with numebr of Bins and AD Interval ***********

    headpack->Msg[45] = 0xE8; // Maxdb low byte
    headpack->Msg[46] = 0x03; // Maxdb high byte (system setting)

    headpack->Msg[47] = 0x97; // lockout time low byte
    headpack->Msg[48] = 0x03; // lockout time high byte (total of 919 usec)

    headpack->Msg[49] = 0x40; // Minoraxis. Ignore
    headpack->Msg[50] = 0x06; // Minoraxis. Ignore

    headpack->Msg[51] = 1;   // Major axis. always 1 for sonar

    headpack->Msg[52] = 0;  // Control char extension. all bits to 0

    headpack->Msg[53] = 0; // scanZ low char 
    headpack->Msg[54] = 0; // scanZ high char
    // **************** the following should be ignored by the micron *****************
    headpack->Msg[55] = 0;
    headpack->Msg[56] = 0;
    headpack->Msg[57] = 0;
    headpack->Msg[58] = 0;
    headpack->Msg[59] = 0;
    headpack->Msg[60] = 0;
    headpack->Msg[61] = 0;
    headpack->Msg[62] = 0;
    headpack->Msg[63] = 0;
    headpack->Msg[64] = 0;
    headpack->Msg[65] = 0;
    headpack->Msg[66] = 0;
    headpack->Msg[67] = 0;
    headpack->Msg[68] = 0;
    headpack->Msg[69] = 0;
    headpack->Msg[70] = 0;

    // ********************** Message Done ******************
    headpack->Terminator = 0x0A; // Line feed at end of packet

    if ( NULL != pScanSettingsOut )
    {
        *pScanSettingsOut = scanSettings;
    }

    return headpack;
 }


TritecPacket* Micron::convertBytes2Packet(U8* msg) {
      
  TritecPacket* tp = new TritecPacket();
  //copying header
  tp->Header = msg[0];
  // copying hex message length string
  tp->HexMsgLength = new U8[4];
  tp->HexMsgLength[0] = msg[1];
  tp->HexMsgLength[1] = msg[2];
  tp->HexMsgLength[2] = msg[3];
  tp->HexMsgLength[3] = msg[4];
  //copying binary value of message length
  tp->MsgLength = new U8[2];
  tp->MsgLength[0] = msg[5];  // low char comes first
  tp->MsgLength[1] = msg[6];
  // copying sender id
  tp->TxNdeID = msg[7]; // shoould be 255 if pc, 02 if sonar
  // copying receiver id
  tp->RxNdeID = msg[8]; // should be 02 if sonar, 255 if pc
  // copying actual message bytes (including command)
  tp->MsgBytes = msg[9]; // may not remaining bytes in responses!
  // now copying message
  int msgpayldlen = tp->MsgLength[0]+256*(tp->MsgLength[1])-5; // just the message payload (start at command code)
  tp->Msg = new U8[msgpayldlen];
  int i;
  for (i = 0; i < msgpayldlen; i++)
       tp->Msg[i] = msg[10 + i];
   // message copied
   tp->Terminator = msg[10+msgpayldlen]; // it should be a Line Feed (0x0A)
   // packet filled
   return tp;
} 

// member variable methods
void Micron::setState(int state) {
    Micron::state = state;
}

int Micron::getState() {
    return state;
}
    
void Micron::setRegion(eRegion region) 
{
    switch ( region )
    {
        case eR_Front:
        {
            setAngleRange( 2400, 4000 );
            break;
        }
        case eR_Right:
        {
            setAngleRange( 400, 5600 );
            break;
        }
        case eR_RearLeft:
        {
            setAngleRange( 0, 800 );
            break;
        }
        case eR_RearRight:
        {
            setAngleRange( 5600, 0 );
            break;
        }
        case eR_Left:
        {
            setAngleRange( 800, 2400 );
            break;
        }
        case eR_Full:
        {
            setAngleRange( 0, MAX_SONAR_ANGLE - SONAR_STEP_ANGLE );
            break;
        }
        default:
        {
            assert( false && "Unhandled region encountered" );
        }
    }
}

void Micron::setAngleRange( S32 startAngle, S32 endAngle )
{
    mStartAngle = startAngle % MAX_SONAR_ANGLE;
    mEndAngle = endAngle % MAX_SONAR_ANGLE;
  
    S32 angleDiff = mEndAngle - mStartAngle;
    while ( angleDiff < 0 )   // Get the difference as a +ve value
    {
        angleDiff += MAX_SONAR_ANGLE;
    }
    
    // This bit of code makes sure that the step angle exactly divides the
    // difference between mStartAngle and mEndAngle
    int numRays = angleDiff / SONAR_STEP_ANGLE;
    mEndAngle = (mStartAngle + numRays*SONAR_STEP_ANGLE)%MAX_SONAR_ANGLE;
}
    
void Micron::setResolution(int resolution) {
    setNumBins( convertResolutionToNumBins( mRange, resolution ) );
}

int Micron::getResolution() const {
    return convertNumBinsToResolution( mRange, mNumBins );
}

void Micron::setNumBins( S32 numBins )
{
    setRangeAndNumBins( mRange, numBins );
}

void Micron::setRange(int range) 
{    
    setRangeAndNumBins( range, mNumBins );
}

int Micron::getRange() {
    return mRange;
}
 
void Micron::setRangeAndResolution( S32 range, S32 resolution )
{
    setRangeAndNumBins( range, convertResolutionToNumBins( range, resolution ) );
}
 
void Micron::setRangeAndNumBins( S32 range, S32 numBins )
{
    if ( range < MIN_RANGE )
    {
        range = MIN_RANGE;
    }
    if ( range > MAX_RANGE )
    {
        range = MAX_RANGE;
    }
    
    if ( numBins < MIN_NUM_BINS )
    {
        numBins = MIN_NUM_BINS;
    }
    if ( numBins > MAX_NUM_BINS )
    {
        numBins = MAX_NUM_BINS;
    }
    
    if ( calculateADInterval( range, numBins ) >= MIN_AD_INTERVAL )
    {
        // The AD interval is achievable
        mRange = range;
        mNumBins = numBins;
    }
}
 
void Micron::setADlow(int adlow) {
    Micron::mADlow = adlow;
}

int Micron::getADlow() {
    return mADlow;
}
    
void Micron::setADspan(int adspan) {
    mADspan = adspan;
}

int Micron::getADspan() {
    return mADspan;
}

void Micron::setGain( F32 gain )
{
    mGain = gain;
    if ( mGain < 0.0f )
    {
        mGain = 0.0f;
    }
    else if ( mGain > 1.0f )
    {
        mGain = 1.0f;
    }
}

F32 Micron::getGain() const
{
    return mGain;
}
    
void Micron::printState() {
    
 printf( "MICRON STATE: ");
    
    switch(state) {
        case stIdle : printf("IDLE");
                      break;
        case stAliveSonar: printf("ALIVE SONAR");
                           break;
        case stExpectAlive: printf ("EXPECTING ALIVE");
                            break;
        case stSendingData: printf("SENDING DATA");
                            break;
        case stExpectHeadData: printf("EXPECTING HEAD DATA");
                                break;
        case stExpectUserData: printf("EXPECTING USER DATA");
                               break;
        case stDataReady: printf("DATA READY");
                         break;
    }
    printf ("\n"); 
} 

S32 Micron::calculateADInterval( S32 range, S32 numBins )
{
    double pingtime = 2.0 * range * 1000.0 / 1.5; // in usec
    double bintime = pingtime / numBins;
    return round( (bintime/64.0)*100.0 );
}

S32 Micron::convertResolutionToNumBins( S32 range, S32 resolution )
{
    return (range * 100) / resolution;
}

S32 Micron::convertNumBinsToResolution( S32 range, S32 numBins )
{
    return (range * 100) / numBins;
}

// member variable methods done






            
     