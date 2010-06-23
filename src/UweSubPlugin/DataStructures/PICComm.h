#ifndef PICCOMM_H
#define PICCOMM_H
 
#include "PICPacket.h"
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include "Common.h"
#include <libplayercore/playercore.h>


class PICComm {
        // ******** Message Type Constants *****************
        public: static const U8 msgGyro = 0;
        public: static const U8 msgAccelerometerX = 1;
        public: static const U8 msgAccelerometerY = 2;
        public: static const U8 msgSonarEcho = 3;
        // ******* Message Type ends ***********************

        public: static PICPacket* convertBytes2Packet(U8* rawmsg);
        public: static void disposePacket(PICPacket* pack);
    };


#endif
