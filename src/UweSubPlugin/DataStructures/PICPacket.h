
#ifndef PICPACKET_H
#define PICPACKET_H

#include "../../Common.h"


typedef struct {
     U8 Starter;
     U32 MsgLen;
     U8 MsgType;
     U8* Message;
    
    }PICPacket;


#endif
