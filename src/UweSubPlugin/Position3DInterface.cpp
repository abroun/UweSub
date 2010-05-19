//------------------------------------------------------------------------------
// File: Position3DInterface.cpp
// Desc: An interface that allows Player to move the AUV
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include "Common.h"
#include "Position3DInterface.h"

#include <stdio.h>
#include "UweSubDriver.h"

#include "roboard.h"
#include "pwm.h"

//------------------------------------------------------------------------------
const U32 Position3DInterface::PWM_FREQUENCY_US = 20000;
const U32 Position3DInterface::MIN_DUTY_CYCLE_US = 1000;
const U32 Position3DInterface::MAX_DUTY_CYCLE_US = 2000;
const U32 Position3DInterface::ZERO_DUTY_CYCLE_US = (MIN_DUTY_CYCLE_US + MAX_DUTY_CYCLE_US)/2;

const U32 Position3DInterface::LEFT_MOTOR_CHANNEL = 2;
const U32 Position3DInterface::TEST_CHANNEL = 16;

const F32 Position3DInterface::MAX_ABS_FORWARD_SPEED = 1.0f;

//------------------------------------------------------------------------------
Position3DInterface::Position3DInterface( player_devaddr_t addr, 
    UweSubDriver* pDriver, ConfigFile* pConfigFile, int section )
    : UweSubInterface( addr, pDriver, pConfigFile, section )
{
    if ( !pwm_Initialize( 0xffff, PWMCLOCK_50MHZ, PWMIRQ_DISABLE ) ) 
    {
        printf( "Unable to initialise PWM library - %s\n", roboio_GetErrMsg() );
    }
    else
    {
        printf( "PWM library initialised\n" );
        
        // Set the channels to produce a zero velocity PWM
        pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US );
        pwm_SetPulse( TEST_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US );
        pwm_SetCountingMode( LEFT_MOTOR_CHANNEL, PWM_CONTINUE_MODE );
        pwm_SetCountingMode( TEST_CHANNEL, PWM_CONTINUE_MODE );
        
        // Enable the pins
        pwm_EnablePin( LEFT_MOTOR_CHANNEL );
        pwm_EnablePin( TEST_CHANNEL );
        
        printf( "All go\n" );
        //printf( "Outputting many pulses\n" );
        pwm_EnableMultiPWM(0xffffffffL);
        printf( "Enabled everything\n" );
    }
}

//------------------------------------------------------------------------------
Position3DInterface::~Position3DInterface()
{
}

//------------------------------------------------------------------------------
// Handle all messages.
int Position3DInterface::ProcessMessage( QueuePointer& respQueue,
                                        player_msghdr_t* pHeader, void* pData )
{
    // New motor command - velocity
    if( Message::MatchMessage( pHeader, PLAYER_MSGTYPE_CMD, 
                           PLAYER_POSITION3D_CMD_SET_VEL, 
                           mDeviceAddress ) )
    {
        player_position3d_cmd_vel_t* pCmd = (player_position3d_cmd_vel_t*)pData;
        
        F32 forwardSpeed = (F32)pCmd->vel.px;
        if ( forwardSpeed > MAX_ABS_FORWARD_SPEED )
        {
            forwardSpeed = MAX_ABS_FORWARD_SPEED;
        }
        else if ( forwardSpeed < -MAX_ABS_FORWARD_SPEED )
        {
            forwardSpeed = -MAX_ABS_FORWARD_SPEED;
        }
        
        // Calculate the PWM to output
        F32 normalisedPWM = (forwardSpeed + MAX_ABS_FORWARD_SPEED) / (2.0f*MAX_ABS_FORWARD_SPEED);
        U32 pwmDuty = MIN_DUTY_CYCLE_US + (U32)(normalisedPWM*(MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US));
        
        pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, pwmDuty );
        pwm_SetPulse( TEST_CHANNEL, PWM_FREQUENCY_US, pwmDuty );
        
        printf( "Sending %ius pulse\n", pwmDuty );

        return 0;
    }
    // Request to enable motor power
    else if( Message::MatchMessage( pHeader, PLAYER_MSGTYPE_REQ, 
                                PLAYER_POSITION3D_REQ_MOTOR_POWER, 
                                mDeviceAddress ) )
    {
        printf( "Ignoring motor request" );
        mpDriver->Publish( mDeviceAddress, respQueue, 
                         PLAYER_MSGTYPE_RESP_NACK, 
                         PLAYER_POSITION3D_REQ_MOTOR_POWER );
        return 0;
    }

 
    
    printf( "Unhandled message\n" );
    return -1;
}


//------------------------------------------------------------------------------
// Update this interface and publish new info.
void Position3DInterface::Update()
{
    // We don't actually publish anything useful here. After all, we don't know
    // yet if the Sub will do anything other than just take desired velocity
    // commands. However, some clients will block till they get fresh data...
    player_position3d_data_t data;

    data.pos.px = 0.0;
    data.pos.py = 0.0;
    data.pos.pz = 0.0;

    data.pos.proll = 0.0;
    data.pos.ppitch = 0.0;
    data.pos.pyaw = 0.0;

    data.vel.px = 0.0;
    data.vel.py = 0.0;
    data.vel.pz = 0.0;

    data.vel.proll = 0.0;
    data.vel.ppitch = 0.0;
    data.vel.pyaw = 0.0;

    data.stall = (uint8_t)0;

    mpDriver->Publish( this->mDeviceAddress,
                       PLAYER_MSGTYPE_DATA, PLAYER_POSITION3D_DATA_STATE,
                       (void*)&data, sizeof( data ) );
}




