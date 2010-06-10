
#ifndef TRITECPACKET_H
#define TRITECPACKET_H

#include "../../Common.h"

typedef struct 
    {
        U8 Header;           // packer header. always '@'
        U8* HexMsgLength;   // Length in hex as a string of 4 characters
        U8* MsgLength;      // Length of packet as an unsigned int (16 bit)
        U8 TxNdeID;         // Packet sender ID (0-255)
        U8 RxNdeID;           // Packet Destination ID (0-255)
        U8 MsgBytes;         // Message length
        U8* Msg;            // The message
        U8 Terminator;       // Message terminator. Should be a Line Feed (0x0A)

    } TritecPacket;


#endif