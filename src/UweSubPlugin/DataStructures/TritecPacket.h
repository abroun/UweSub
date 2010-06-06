

typedef struct 
    {
        char Header;           // packer header. always '@'
        char* HexMsgLength;   // Length in hex as a string of 4 characters
        char* MsgLength;      // Length of packet as an unsigned int (16 bit)
        char TxNdeID;         // Packet sender ID (0-255)
        char RxNdeID;           // Packet Destination ID (0-255)
        char MsgBytes;         // Message length
        char* Msg;            // The message
        char Terminator;       // Message terminator. Should be a Line Feed (0x0A)

    } TritecPacket;

