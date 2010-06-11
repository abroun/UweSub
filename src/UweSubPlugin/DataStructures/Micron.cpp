
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

// Operation constants
 const U8 Micron::leftRegion = 0;  // 135 to 225 degrees
 const U8 Micron::frontRegion = 1; //45 to 135 degrees 
 const U8 Micron::rightRegion = 2; // -45 to 45 degrees
 const U8 Micron::rearLeftRegion = 3;  // 235 to 270 degrees
 const U8 Micron::rearRightRegion = 4; // 270 to 315 degrees

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


// parametric constructor
Micron::Micron(int range, int resolution, int ADlow, int ADspan) {
            
    Micron::range = range;
    Micron::resolution = resolution;
    Micron::ADlow = ADlow;
    Micron::ADspan = ADspan;
    
    // setting regionBins lines to NULL
    for (int i=0; i<MAX_LINES; i++) regionBins[i] = NULL;
    // setting state and selected region to scan
    state = stIdle;
    currentRegion = frontRegion;
}

// default values constructor
Micron::Micron() {
    Micron::range = 20; // 20 m standard range
    Micron::resolution = 5; // 5 cm standard resolution
    Micron::ADlow = 40;     // 40 dB standard AD low limit
    Micron::ADspan = 24;    // 24 dB  standard AD span
   
    // setting regionBins lines to NULL
    for (int i=0; i<MAX_LINES; i++) 
            Micron::regionBins[i] = NULL;
   
    state = stAliveSonar; // starting from alive state. Assumming Sonar connected and powered
    currentRegion = frontRegion;
}


Micron::~Micron() {
  // disposing scannedlines  
  int i;
  for (i=0; i<scannedlines; i++)
      if (regionBins[i]!=NULL) delete [] regionBins[i];
}


// reset (call after a reboot)
void Micron::reset() {
    // disposing bin data if any
    int i;
    for (i=0; i<MAX_LINES; i++) 
        if (regionBins[i]!=NULL) {
            delete [] regionBins[i];
            regionBins[i] = NULL;
        }
    // setting current region to frontRegion
    currentRegion = frontRegion;
    scannedlines = 0;
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
void Micron::sendHeadCommand(Device* theOpaque, QueuePointer inqueue, U8 region) {
       // creating the head packet
       TritecPacket* headpack = makeHead(range, region, resolution, ADlow, ADspan);
       // retrieving length
       int len = packetLength(headpack);
       // converting to raw data
       U8* headraw = convertPacket2Bytes(headpack);
       // now allocating the region array of bins
       currentRegion = region;
       // disposing old region if not null
       for (int i=0; i<MAX_LINES; i++)
          if (regionBins[i]!=NULL) {
                delete [] regionBins[i];
                regionBins[i] = NULL;
            }
       // initializing scannedlines
       scannedlines = 0;
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


// this function clears regionBins and scannedlines
void Micron::clearRegionBins()
{
    int i;
    for (i=0; i<MAX_LINES; i++)
        if (regionBins[i]!=NULL) {
            delete [] regionBins[i];
            regionBins[i] = NULL;
        }
   scannedlines = 0;
}

// this function expands the current region array of bins
void Micron::addScanLine(U8* line, int len) {
         
         regionBins[scannedlines - 1] = new U8[len];
         for (int i=0; i<len; i++) regionBins[i] = regionBins[i];
         
         delete [] line;
}

// this functions changes state according to the response from the sonar
void Micron::transitionAction(TritecPacket* pack, Device* theOpaque, QueuePointer inqueue) {
        U8 cmd = pack->Msg[0]; // get command

        int datalen=0, headofs=0;
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
                                scannedlines = 0; // reseting scannedlines
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
                            scannedlines = 0; // should be already zero, just in case...
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
                            linebins = unwrapHeadData(pack, datalen, headofs);
                            scannedlines++;
                            printf ("Data unwrapped.Scanned Lines: %i\n",scannedlines );
                            addScanLine(linebins, datalen);
                            
                            if ((currentRegion==rearLeftRegion)||(currentRegion==rearRightRegion)) {
                                if (scannedlines==50) state = stDataReady;
                                    else if (scannedlines % 2 ==0) {
                                        
                                        Micron::sendData(theOpaque, inqueue); 
                                        for (int d=0; d<20000; d++);
                                        state = stSendingData; // not needed as sendData() takes care...
                                    }
                                        else state = stExpectHeadData;
                            } else {
                                if (scannedlines==100) state = stDataReady;
                                    else if (scannedlines % 2 == 0) {
                                        
                                        Micron::sendData(theOpaque, inqueue);
                                        for (int d=0; d<20000; d++);
                                        state = stSendingData; // not needed as sendData() takes care...
                                    }   
                                     else state = stExpectHeadData;
                            }
                            break;
                        case stSendingData: // in the case we receive a second head data (full duplex)
                            linebins = unwrapHeadData(pack, datalen, headofs);
                            scannedlines++;
                            printf("Data unwrapped. Scanned lines: %i\n",scannedlines);
                            // adding line to the region array
                            addScanLine(linebins, datalen);
                            
                            if ((currentRegion==rearLeftRegion)||(currentRegion==rearRightRegion)) {
                                if (scannedlines == 50) state = stDataReady;
                                    else if (scannedlines % 2 ==0) {
                                        
                                        Micron::sendData(theOpaque, inqueue);
                                        for (int d=0; d<20000; d++);
                                        state = stSendingData; // not needed as sendData() takes care...
                                    }
                                     else state = stExpectHeadData;
                            } else {
                                if (scannedlines == 100) state = stDataReady;
                                    else if (scannedlines % 2 ==0) {
                                        
                                        Micron::sendData(theOpaque, inqueue);
                                        for (int d=0; d<20000; d++);
                                        state = stSendingData; // not needed as sendData() takes care...
                                    }
                                        else state = stExpectHeadData;
                            }
                            break;
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



U8* Micron::unwrapHeadData(TritecPacket* hdatapack, int& datalen, int& headofs) {
      
    datalen = hdatapack->Msg[32] + 256 * hdatapack->Msg[33];
    headofs = hdatapack->Msg[21] + 256 * hdatapack->Msg[22];
    int i;
    U8* bins = new U8[datalen];
    for (i = 0; i < datalen; i++)
                bins[i] = hdatapack->Msg[34 + i];
    return bins;
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
TritecPacket* Micron::makeHead(int range, U8 region, int resolution, int ADlow, int ADspan) {
     
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
  headpack->Msg[4] = 0x05;
  // bit 0:     1  ADC 8-bit
  // bit 1:     0  Sector Scan
  // bit 2:     1  for right scan, 0 for left scan (here set 1 orginally for masking)
  // bit 3:     0  ignored when doing sector scan
  // bit 4:     0  motor enabled (makes no difference in the micron)
  // bit 5:     0  sonar transmitter enabled
  // bit 6:     0  always
  // bit 7:     0  low Frequency channel

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

  int leftlim = 0, rightlim = 0;
  if (region == Micron::frontRegion) 
  {
       leftlim = 2400;
       rightlim = 4000;
   } 
    else if (region == Micron::rightRegion)
            {
                leftlim = 400;
                rightlim = 5600;
            }
	      else if (region == Micron::rearLeftRegion)
		{
		  leftlim = 0;
		  rightlim = 800;
		}
		else if (region == Micron::rearRightRegion)
		  {
		    leftlim = 5600;
		    rightlim = 6399;
		  }
		   else if (region == Micron::leftRegion)
		      {
                leftlim = 800;
                rightlim = 2400;
		      }
        
   headpack->Msg[27] = (U8)(leftlim & 0xFF);
   headpack->Msg[28] = (U8)((leftlim >> 8) & 0xFF);
   headpack->Msg[29] = (U8)(rightlim & 0xFF);
   headpack->Msg[30] = (U8)((rightlim >> 8) & 0xFF);

   // calculating AdLow and AdSpan
   headpack->Msg[31] = (U8)(ADspan * 255 / 80); // AD span in range 0-255
   headpack->Msg[32] = (U8)(ADlow * 255 / 80); // AD low in range 0-255

   headpack->Msg[33] = 0x54; // initial gain for channel #1
   headpack->Msg[34] = 0x54; // initial gain for channel #2

   headpack->Msg[35] = 0x5A; // channel 1 slope low char, ignored
   headpack->Msg[36] = 0x00; // channel 1 slope high char, ignored

   headpack->Msg[37] = 0x7D; // channel 2 slope low byte, ignored
   headpack->Msg[38] = 0x00; // channel 2 slope high byte, ignored

   headpack->Msg[39] = 0x20; // 3.2 usec motor step time
   headpack->Msg[40] = 16; // 16 steps. For a 90 degree region, we get 100 lines 0.9 degrees apart

   // ******** now caculating AD interval and Number of Bins **************
   int Nbins = range*100/resolution;
   double pingtime = 2 * range * 1000 / 1.5; // in usec
   double bintime = pingtime / Nbins;
   int ADinterval = (bintime/64)*100;


   headpack->Msg[41] = (U8)(ADinterval & 0xFF); // AD interval low byte. 
   headpack->Msg[42] = (U8)((ADinterval >> 8) & 0xFF);  // AD interval high byte

   headpack->Msg[43] = (U8)(Nbins & 0xFF); // Number of Bins Low byte
   headpack->Msg[44] = (U8)((Nbins >> 8) & 0xFF); // Number of Bins high byte

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
    
void Micron::setRegion(U8 region) {
    Micron::currentRegion = region;
}

U8 Micron::getRegion() {
    return Micron::currentRegion;
}
    
void Micron::setResolution(int resolution) {
    Micron::resolution = resolution;
}

int Micron::getResolution() {
    return resolution;
}

void Micron::setRange(int range) {
    Micron::range = range;
}

int Micron::getRange() {
    return range;
}
    
void Micron::setADlow(int adlow) {
    Micron::ADlow = adlow;
}

int Micron::getADlow() {
    return ADlow;
}
    
void Micron::setADspan(int adspan) {
    ADspan = adspan;
}

int Micron::getADspan() {
    return ADspan;
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
// member variable methods done



            
     