
#ifndef MICRON_H
#define MICRON_H

#include "TritecPacket.h"
#include <stdlib.h>
#include <stdio.h>
#include "../../Common.h"
#include <libplayercore/playercore.h>


    
class Micron {

       // Tritec Protocol Command Constants
       private: static const U8 mtVersionData; // Version reply by the micron
       private: static const U8 mtHeadData; // Head data reply by the micron
       private: static const U8 mtAlive;    // Alive reply by the micron
       private: static const U8 mtBBUserData; // User data reply by the micron
       private: static const U8 mtReBoot; // Reboot sonar
       private: static const U8 mtHeadCommand; // configure the micron for scanning
       private: static const U8 mtSendVersion;  // request parameters from micron
       private: static const U8 mtSendBBUser; // request user data from micron
       private: static const U8 mtSendData;   // request half/full duplex data from micron
       private: static const U8 mtStopAlive; // forces micron to stop sedning repeated alive msgs
        
       // Commands ends

       // Operation constants
       public: static const U8 leftRegion;  // 135 to 225 degrees
       public: static const U8 frontRegion; //45 to 135 degrees 
       public: static const U8 rightRegion; // -45 to 45 degrees
       public: static const U8 rearLeftRegion;  // 235 to 270 degrees
       public: static const U8 rearRightRegion; // 270 to 315 degrees

       // alive constants (for evaluation of an mtAlive Message)
       public: static const U8 alFalseAlive;
       public: static const U8 alNoParams;
       public: static const U8 alParamsAck;
       public: static const U8 alInScan;

       // maximum number of lines constant
       private: static const int MAX_LINES=100;
	
       // class members
       private: int state;
                int range;
                int resolution;
                int ADlow;
                int ADspan;

       public: U8 currentRegion;
       public: int scannedlines;
       public: U8* regionBins[MAX_LINES];

       // state constants
       public: static const int stIdle;
       public: static const int stConnected;
       public: static const int stExpectAlive;
       public: static const int stAliveSonar;
       public: static const int stExpectHeadAlive;
       public: static const int stSendingData;
       public: static const int stExpectHeadData;
       public: static const int stExpectUserData;
       public: static const int stDataReady;
  
     
  
                // parametric constructor
        public: Micron(int range, int resolution, int ADlow, int ADspan);
        
                // default values constructor
                Micron();
        
                // Micron Destructor
                ~Micron(); 
    
         // a method to reset the micron to it's default (must be used after a reboot)
        public: void reset();
         
        // ******** The following functions send packages to the micron via a designated channel (use of opaque)******
        
       // send BB user Data 
       public: void sendBBUser(Device* theOpaque, QueuePointer inqueue);
        
        // this function kills the constant alive messages from the micron
        public: void sendStopAlives(Device* theOpaque, QueuePointer inqueue); 
        
       
        //this function reboots the micron
        public: void sendReboot(Device* theOpaque, QueuePointer inqueue);
        

        // this function sends an mtSendVersion command
        public: void sendVersion(Device* theOpaque, QueuePointer inqueue);
      

        // this function sends an mtHeadCommand
        public: void sendHeadCommand(Device* theOpaque, QueuePointer inqueue ,U8 region);
        

        // this functions sends a sendData command
        public: void sendData(Device* theOpaque, QueuePointer inqueue);
        
        // **************************** Send Package Functions ends here ********************************

        // **************************** Internal Class State and Data Handling ************************** 
          
        // this function expands the current region array of bins
        private: void addScanLine(U8* line);
        
	    // this function changes internal state
        public: void transitionAction(TritecPacket* pack, Device* theOpaque, QueuePointer inqueue);

        // ************************ State and Data Handling functions ends here **************************
        
        // this function returns the total length of a packet in bytes
        public: static int packetLength(TritecPacket* tp);
        
        // This function converts a packet to a raw bytes message
	    public: static U8* convertPacket2Bytes(TritecPacket* tp);
	
	    // This function makes a packet out of raw bytes
        public: static TritecPacket* convertBytes2Packet(U8* msg);
        
        // This function disposes a tritech Packet
        public: static void disposePacket(TritecPacket* pack);

	// ************************* Methods that create micron command packets ********************	

	    // mtReboot Command Packet
	    public: static TritecPacket* makeReboot();
        
	   // mtSendVesrion Command packet
        public: static TritecPacket* makeSendVersion();

	    // mtStopAlives command packet
        public: static TritecPacket* makeStopAlives();
        
	     // mtSendData command packet
	    public: static TritecPacket* makeSendData();
	
	     // mtHeadData command packet. specify resolution in cms, range in meters
        public: static TritecPacket* makeHead(int range, U8 region, int resolution, int ADlow, int ADspan);
        
        // An mtSendBBUser command packet
        public: static TritecPacket* makeSendBBUser();
	// **************************** Command Packets Methods ends here ********************************


	// ******************************** Packet Handling methods **************************************

	// This function returns a scanned line as an array of characters from a HeadData packet        
	public: static U8* unwrapHeadData(TritecPacket* hdatapack, int& datalen, int& headofs);
        
	// This function recognizes the type of an alive message returned by the micron
        public: static int validateAlive(TritecPacket* alivepack);
	// Packet Handling methods ends here     
	
	// member variable methods
    public: void setState(int state);
    public: int getState();
    
    public: void setRegion(U8 region);
    public: U8 getRegion();
    
    public: void setResolution(int resolution);
    public: int getResolution();
     
    public: void setRange(int range);
    public: int getRange();
    
    public: void setADlow(int adlow);
    public: int getADlow();
    
    public: void setADspan(int adspan);
    public: int getADspan();
    
    public: void printState();
    // member variable methods done

	    
 }; // class definition ends here 

#endif // Header ends here
