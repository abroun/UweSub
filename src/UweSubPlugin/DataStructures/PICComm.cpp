#include "PICComm.h"



PICPacket* PICComm::convertBytes2Packet(U8* rawmsg) {
            U32 i;
            PICPacket* pack = new PICPacket();

            pack->Starter = rawmsg[0];
            pack->MsgLen = (U32)rawmsg[1] + (U32)(256 * rawmsg[2]);
            pack->MsgType = rawmsg[3];
            pack->Message = new U8[pack->MsgLen - 3];
            for (i = 0; i < pack->MsgLen - 3; i++)
                pack->Message[i] = rawmsg[4 + i];

            return pack;
        }

void PICComm::disposePacket(PICPacket* pack) {
    // disposing message
    delete [] pack->Message;
    // disposing packet
    delete [] pack;
}
