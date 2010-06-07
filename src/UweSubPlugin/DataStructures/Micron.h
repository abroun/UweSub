
#ifndef MICRON_H
#define MICRON_H

#include "TritecPacket.h"
#include <stdlib.h>
#include <libplayercore/playercore.h>


    
class Micron {

       // Tritec Protocol Command Constants
       private: const char mtVersionData; // Version reply by the micron
       private: const char mtHeadData; // Head data reply by the micron
       private: const char mtAlive;    // Alive reply by the micron
       private: const char mtBBUserData; // User data reply by the micron
       private: const char mtReBoot; // Reboot sonar
       private: const char mtHeadCommand; // configure the micron for scanning
       private: const char mtSendVersion;  // request parameters from micron
       private: const char mtSendBBUser; // request user data from micron
       private: const char mtSendData;   // request half/full duplex data from micron
       private: const char mtStopAlive; // forces micron to stop sedning repeated alive msgs
        
       // Commands ends

       // Operation constants
       public: static const char leftRegion;  // 135 to 225 degrees
       public: static const char frontRegion; //45 to 135 degrees 
       public: static const char rightRegion; // -45 to 45 degrees
       public: static const char rearLeftRegion;  // 235 to 270 degrees
       public: static const char rearRightRegion; // 270 to 315 degrees

       // alive constants (for evaluation of an mtAlive Message)
       public: static const char alFalseAlive;
       public: static const char alNoParams;
       public: static const char alParamsAck;
       public: static const char alInScan;

       // maximum number of lines constant
       private: const int MAX_LINES;
	
       // class members
       private: int state;
                int range;
                int resolution;
                int ADlow;
                int ADspan;

       public: char currentRegion;
       public: int scannedlines;
       public: char* regionBins[];

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
        
        // this function kills the constant alive messages from the micron
        public: void sendStopAlives(Device* theOpaque, QueuePointer inqueue); 
        
       
        //this function reboots the micron
        public: void sendReboot(Device* theOpaque, QueuePointer inqueue);
        

        // this function sends an mtSendVersion command
        public: void sendVersion(Device* theOpaque, QueuePointer inqueue);
      

        // this function sends an mtHeadCommand
        public: void sendHeadCommand(Device* theOpaque, QueuePointer inqueue ,char region);
        

        // this functions sends a sendData command
        public: void sendData(Device* theOpaque, QueuePointer inqueue);
        
        // **************************** Send Package Functions ends here ********************************

        // **************************** Internal Class State and Data Handling ************************** 
          
        // this function expands the current region array of bins
        private: void addScanLine(char* line);
        
	    // this function changes internal state
        public: void transitionAction(TritecPacket* pack);

        // ************************ State and Data Handling functions ends here **************************
        
        // this function returns the total length of a packet in bytes
        public: static int packetLength(TritecPacket* tp);
        
        // This function converts a packet to a raw bytes message
	    public: static char* convertPacket2Bytes(TritecPacket* tp);
	
	    // This function makes a packet out of raw bytes
        public: static TritecPacket* convertBytes2Packet(char* msg);

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
        public: static TritecPacket* makeHead(int range, char region, int resolution, int ADlow, int ADspan);
	// **************************** Command Packets Methods ends here ********************************


	// ******************************** Packet Handling methods **************************************

	// This function returns a scanned line as an array of characters from a HeadData packet        
	public: static char* unwrapHeadData(TritecPacket* hdatapack, int& datalen, int& headofs);
        
	// This function recognizes the type of an alive message returned by the micron
        public: static int validateAlive(TritecPacket* alivepack);
	// Packet Handling methods ends here     
	
	// member variable methods
    public: void setState(int state);
    public: int getState();
    
    public: void setRegion(char region);
    public: char getRegion();
    
    public: void setResolution(int resolution);
    public: int getResolution();
    
    public: void setRange(int range);
    public: int getRange();
    
    public: void setADlow(int adlow);
    public: int getADlow();
    
    public: void setADspan(int adspan);
    public: void getADspan();
    // member variable methods done

	    
 }; // class definition ends here 

#endif // Header ends here
