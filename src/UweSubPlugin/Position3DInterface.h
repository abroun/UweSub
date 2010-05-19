//------------------------------------------------------------------------------
// File: Position3DInterface.h
// Desc: An interface that allows Player to move the AUV
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef POSITION_3D_INTERFACE_H
#define POSITION_3D_INTERFACE_H

//------------------------------------------------------------------------------
#include "Common.h"
#include "UweSubInterface.h"

//------------------------------------------------------------------------------
class Position3DInterface : public UweSubInterface
{
    // Constructor
    public: Position3DInterface( player_devaddr_t addr, UweSubDriver* pDriver,
                              ConfigFile* pConfigFile, int section );
    // Destructor
    public: virtual ~Position3DInterface();

    // Handle all messages.
    public: virtual int ProcessMessage( QueuePointer &respQueue,
                                      player_msghdr_t* pHeader, void* pData );

    // Update this interface, publish new info.
    public: virtual void Update();
    
    private: static const U32 PWM_FREQUENCY_US;
    private: static const U32 MIN_DUTY_CYCLE_US;
    private: static const U32 MAX_DUTY_CYCLE_US;
    private: static const U32 ZERO_DUTY_CYCLE_US;
    
    private: static const U32 LEFT_MOTOR_CHANNEL;
    private: static const U32 TEST_CHANNEL;
    
    private: static const F32 MAX_ABS_FORWARD_SPEED;
};

#endif // POSITION_3D_INTERFACE_H