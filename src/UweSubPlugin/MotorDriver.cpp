//------------------------------------------------------------------------------
// File: MotorDriver.h
// Desc: A driver for controlling the motors of the AUV using PWM signals
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include "MotorDriver.h"
#include "roboard.h"
#include "pwm.h"

//------------------------------------------------------------------------------
// A factory creation function, declared outside of the class so that it
// can be invoked without any object context (alternatively, you can
// declare it static in the class).  In this function, we create and return
// (as a generic Driver*) a pointer to a new instance of this driver.
Driver* MotorDriverInit( ConfigFile* pConfigFile, int section )
{
    // Create and return a new instance of this driver
    return (Driver*)(new MotorDriver( pConfigFile, section ));
}

//------------------------------------------------------------------------------
// A driver registration function, again declared outside of the class so
// that it can be invoked without object context.  In this function, we add
// the driver into the given driver table, indicating which interfaces the
// driver can support and how to create a driver instance.
void MotorDriverRegister( DriverTable* pTable )
{
    pTable->AddDriver( (char*)"motordriver", MotorDriverInit );
}

//------------------------------------------------------------------------------
// MotorDriver
//------------------------------------------------------------------------------
const U32 MotorDriver::PWM_FREQUENCY_US = 20000;
const U32 MotorDriver::MIN_DUTY_CYCLE_US = 1000;
const U32 MotorDriver::MAX_DUTY_CYCLE_US = 2000;
const U32 MotorDriver::ZERO_DUTY_CYCLE_US = (MIN_DUTY_CYCLE_US + MAX_DUTY_CYCLE_US)/2;

const U32 MotorDriver::LEFT_MOTOR_CHANNEL = 2;
const U32 MotorDriver::TEST_CHANNEL = 16;

const F32 MotorDriver::MAX_ABS_FORWARD_SPEED = 1.0f;

//------------------------------------------------------------------------------
// Constructor.  Retrieve options from the configuration file and do any
// pre-Setup() setup.
MotorDriver::MotorDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_POSITION3D_CODE ),
    mbInitialisedPWM( false )
{
    this->alwayson = true;
    
    if ( !pwm_Initialize( 0xffff, PWMCLOCK_50MHZ, PWMIRQ_DISABLE ) ) 
    {
        printf( "Unable to initialise PWM library - %s\n", roboio_GetErrMsg() );
    }
    else
    {
        printf( "PWM library initialised\n" );
        mbInitialisedPWM = true;
        
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
MotorDriver::~MotorDriver()
{
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int MotorDriver::MainSetup()
{
    return 0;
}


//------------------------------------------------------------------------------
// Shutdown the device
void MotorDriver::MainQuit()
{
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int MotorDriver::ProcessMessage( QueuePointer& respQueue,
                                player_msghdr* pHeader, void* pData )
{   
    // New motor command - velocity
    if( Message::MatchMessage( pHeader, PLAYER_MSGTYPE_CMD, 
                           PLAYER_POSITION3D_CMD_SET_VEL, 
                           this->device_addr ) )
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
        
        if ( mbInitialisedPWM )
        {
            pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, pwmDuty );
            pwm_SetPulse( TEST_CHANNEL, PWM_FREQUENCY_US, pwmDuty );
        }
        
        printf( "Sending %ius pulse\n", pwmDuty );

        return 0;
    }
    // Request to enable motor power
    else if( Message::MatchMessage( pHeader, PLAYER_MSGTYPE_REQ, 
                                PLAYER_POSITION3D_REQ_MOTOR_POWER, 
                                this->device_addr ) )
    {
        printf( "Ignoring motor request" );
        Publish( this->device_addr, respQueue, 
            PLAYER_MSGTYPE_RESP_NACK, 
            PLAYER_POSITION3D_REQ_MOTOR_POWER );
        return 0;
    }
    
    printf( "Unhandled message\n" );
    return -1;
}

//------------------------------------------------------------------------------
// Main function for device thread
void MotorDriver::Main()
{
    for (;;)
    {
        // Wait for messages to arrive
        base::Wait();
        
        base::ProcessMessages();
    }
}

