#ifndef MICRONCMDS_H
#define MICRONCMDS_H

#include <stdlib.h>

// Micron command codes
typedef enum {
        micronREBOOT,               // Reboot the sonar
        micronSET_REGION_FRONT,     // Set current region to FRONT (45 to 135 degrees)
        micronSET_REGION_RIGHT,      // set current region to RIGHT (-45 to 45 degrees)
        micronSET_REGION_LEFT,       // set current region to LEFT (135 to 225 degrees)
        micronSET_REGION_REAR_RIGHT, // set current region to REAR RIGHT (-90 to -45 degrees)
        micronSET_REGION_REAR_LEFT,  // set current region to REAR LEFT (225 to 270 degrees)
        micronSET_RESOLUTION5,       // set Resolution to 5cms
        micronSET_RESOLUTION10,      // set Resolution to 10cms
        micronSET_RESOLUTION20,      // set Resolution to 20cms
        micronSET_RANGE10,           // set Range to 10 meters
        micronSET_RANGE20,           // set Range to 20 meters
        micronSET_RANGE30,           // set Range to 30 meters
        micronSCAN_REGION,            // Do a scan of the selected region
        micronSTREAM_REGION_DATA,     // put region data in the buffer 
        micronCMDS_COUNT,             // commands count
        micronUNRECOGNIZED            // to be used as an error code (unknown command)
}micron_cmd_t;
       
// micron responses
typedef enum {
        micronREGION_SET,       // new region accepted 
        micronRESOLUTION_SET,   // Resolution value accepted 
        micronRANGE_SET,        // new range value accepted
        micronALIVE,            // following a reboot
        micronDATA_READY,        // region scanned
        micronMSGS_COUNT,        // response messages count
        micronMSG_UNKNOWN       // to be used for an unknown message (unrecognized message)
}micron_msg_t;

// command strings
static char micron_cmds[micronCMDS_COUNT][7];
// response strings
static char micron_msgs[micronMSGS_COUNT][7];


micron_cmd_t micronDecodeCommand(char* cmd);

micron_msg_t micronDecodeMsg(char* msg);

#endif
