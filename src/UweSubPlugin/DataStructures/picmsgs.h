#ifndef PICMSGS_H
#define PICMSGS_H
 
#include <stdlib.h>
#include <string.h>
#include "Common.h"


// Micron command codes
typedef enum {
        picFIRE_TRANSDUCER_0,     // Fire Transducer #0
        picFIRE_TRANSDUCER_1,     // Fire Transducer #1
        picLISTEN_TRANSDUCER_0,   // Do a Passive Scan with transducer #0 (No firing)
        picLISTEN_TRANSDUCER_1,   // Do a Passive Scan with tramsducer #1 (No firing)
        picSEND_ANGULAR_VELOCITY, // send angular velocity reading
        picSEND_ACCELERATION_X,   // send acceleration reading on X axis
        picSEND_ACCELERATION_Y,   // send acceleration reading on Y axis
        picCMDS_COUNT,
        picCMD_UNKNOWN
}pic_cmd_t;
     

// command strings
static const char pic_cmds[picCMDS_COUNT][4] = {
         "FS0",
         "FS1",
         "LS0",
         "LS1",
         "ANG",
         "ACX",
         "ACY"
}; 


pic_cmd_t pic_Decode_Cmd(char* msg);

#endif
