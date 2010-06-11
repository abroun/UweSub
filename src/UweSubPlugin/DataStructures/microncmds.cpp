
#include "microncmds.h"
 


// string to command code
micron_cmd_t micronDecodeCommand(char* cmd) {
    micron_cmd_t code;
    if (strcmp(cmd, micron_cmds[micronREBOOT])==0) code = micronREBOOT; 
        else if (strcmp(cmd, micron_cmds[micronSET_REGION_FRONT])==0) code = micronSET_REGION_FRONT; 
            else if (strcmp(cmd, micron_cmds[micronSET_REGION_RIGHT])==0) code = micronSET_REGION_RIGHT;
                else if (strcmp(cmd, micron_cmds[micronSET_REGION_LEFT])==0) code = micronSET_REGION_LEFT;
                    else if (strcmp(cmd, micron_cmds[micronSET_REGION_REAR_RIGHT])==0) code = micronSET_REGION_REAR_RIGHT;
                        else if (strcmp(cmd, micron_cmds[micronSET_REGION_REAR_LEFT])==0) code = micronSET_REGION_REAR_LEFT;
                            else if (strcmp(cmd, micron_cmds[micronSET_RESOLUTION5])==0) code = micronSET_RESOLUTION5;
                                else if (strcmp(cmd, micron_cmds[micronSET_RESOLUTION10])==0) code = micronSET_RESOLUTION10;
                                    else if (strcmp(cmd, micron_cmds[micronSET_RESOLUTION20])==0) code = micronSET_RESOLUTION20;
                                        else if (strcmp(cmd, micron_cmds[micronSET_RANGE10])==0) code = micronSET_RANGE10;
                                            else if (strcmp(cmd, micron_cmds[micronSET_RANGE20])==0) code = micronSET_RANGE20;
                                                else if (strcmp(cmd, micron_cmds[micronSET_RANGE30])==0) code = micronSET_RANGE30;
                                                    else if (strcmp(cmd, micron_cmds[micronSCAN_REGION])==0) code = micronSCAN_REGION;
                                                        else if (strcmp(cmd, micron_cmds[micronSTREAM_REGION_DATA])==0) code = micronSTREAM_REGION_DATA;
                                                            else code = micronUNRECOGNIZED;
              
    return code;
}



// string to message code
micron_msg_t micronDecodeMsg(char* msg) {
    micron_msg_t code;
    if (strcmp(msg, micron_msgs[micronREGION_SET])==0) code = micronREGION_SET;
        else if (strcmp(msg, micron_msgs[micronRESOLUTION_SET])==0) code = micronRESOLUTION_SET;
            else if (strcmp(msg, micron_msgs[micronRANGE_SET])==0) code = micronRANGE_SET;
                else if (strcmp(msg, micron_msgs[micronALIVE])==0) code = micronALIVE;
                    else if (strcmp(msg, micron_msgs[micronDATA_READY])==0) code = micronDATA_READY;
                            else code = micronMSG_UNKNOWN;
                
    return code;
}