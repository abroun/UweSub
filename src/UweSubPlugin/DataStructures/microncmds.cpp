
#include "microncmds.h"
#include "Common.h"


// string to command code
micron_cmd_t micronDecodeCommand(char* cmd) 
{
    micron_cmd_t code = micronUNRECOGNIZED;
    
    for ( S32 cmdIdx = 0; cmdIdx < micronCMDS_COUNT; cmdIdx++ )
    {
        if ( strcmp( cmd, micron_cmds[ cmdIdx ] ) == 0 )
        {
            code = (micron_cmd_t)cmdIdx; 
        }
    }
    
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