//------------------------------------------------------------------------------
// File: MotorDriver.cpp
// Desc: A driver for controlling the motors of the AUV using PWM signals
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include <math.h>
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

const U32 MotorDriver::RIGHT_MOTOR_CHANNEL = 2;    // 01
const U32 MotorDriver::LEFT_MOTOR_CHANNEL = 3;     // 10
const U32 MotorDriver::FRONT_MOTOR_CHANNEL = 4;
const U32 MotorDriver::BACK_MOTOR_CHANNEL = 5;
const U32 MotorDriver::TEST_CHANNEL = 16;

const F32 MotorDriver::MAX_ABS_2D_DIST = 1.0f;
const F32 MotorDriver::MAX_ABS_LINEAR_SPEED = 1.0f;
const F32 MotorDriver::MAX_ABS_ANG_SPEED = M_PI/6;

//------------------------------------------------------------------------------
// Constructor.  Retrieve options from the configuration file and do any
// pre-Setup() setup.
MotorDriver::MotorDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_POSITION3D_CODE ),
    mbCompassAvailable( false ),
    mLastDisplayedCompassAngleTimestamp( 0.0 ),
    mbInitialisedPWM( false )
{
    this->alwayson = true;
    
    if ( !pwm_Initialize( 0xffff, PWMCLOCK_50MHZ, PWMIRQ_DISABLE ) ) 
    {
        printf( "Unable to initialise PWM library - %s\n", roboio_GetErrMsg() );
        mbInitialisedPWM = false;
    }
    else
    {
        printf( "PWM library initialised\n" );
        mbInitialisedPWM = true;
        
        // Set the channels to produce a zero velocity PWM
        pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US );
        pwm_SetPulse( RIGHT_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US );
        pwm_SetPulse( FRONT_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US );
        pwm_SetPulse( BACK_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US );
        pwm_SetPulse( TEST_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US );
        pwm_SetCountingMode( LEFT_MOTOR_CHANNEL, PWM_CONTINUE_MODE );
        pwm_SetCountingMode( RIGHT_MOTOR_CHANNEL, PWM_CONTINUE_MODE );
        pwm_SetCountingMode( FRONT_MOTOR_CHANNEL, PWM_CONTINUE_MODE );
        pwm_SetCountingMode( BACK_MOTOR_CHANNEL, PWM_CONTINUE_MODE );
        pwm_SetCountingMode( TEST_CHANNEL, PWM_CONTINUE_MODE );
        
        // Enable the pins
        pwm_EnablePin( LEFT_MOTOR_CHANNEL );
        pwm_EnablePin( FRONT_MOTOR_CHANNEL );
        pwm_EnablePin( RIGHT_MOTOR_CHANNEL );
        pwm_EnablePin( BACK_MOTOR_CHANNEL );
        pwm_EnablePin( TEST_CHANNEL );
        
        printf( "All go\n" );
        //printf( "Outputting many pulses\n" );
        pwm_EnableMultiPWM(0xffffffffL);
        printf( "Enabled everything\n" );
    }
    
    mpCompass = NULL;
    // See if we have an imu (compass) device
    if ( pConfigFile->ReadDeviceAddr( &mCompassID, section, "requires",
                       PLAYER_IMU_CODE, -1, NULL ) != 0 )
    {
        PLAYER_WARN( "No Compass driver specified" );
    }
    else
    {
        mbCompassAvailable = true;
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
    if ( mbCompassAvailable )
    {
        if ( Device::MatchDeviceAddress( mCompassID, this->device_addr ) )
        {
            PLAYER_ERROR( "Attempting to subscribe to self" );
            return -1;
        }

        mpCompass = deviceTable->GetDevice( mCompassID );
        if ( NULL == mpCompass )
        {
            PLAYER_ERROR( "Unable to locate suitable compass device" );
            return -1;
        }

        if ( mpCompass->Subscribe( this->InQueue ) != 0 )
        {
            PLAYER_ERROR( "Unable to subscribe to compass device" );
            return -1;
        }
    }
    
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
        
        F32 linearSpeed = (F32)pCmd->vel.px;
        if ( linearSpeed > MAX_ABS_LINEAR_SPEED )
        {
           linearSpeed = MAX_ABS_LINEAR_SPEED;
        }
        else if ( linearSpeed < -MAX_ABS_LINEAR_SPEED )
        {
            linearSpeed = -MAX_ABS_LINEAR_SPEED;
        }
        
        F32 speedyaw = (F32)pCmd->vel.pyaw;
        if ( speedyaw > MAX_ABS_ANG_SPEED )
        {
           speedyaw = MAX_ABS_ANG_SPEED;
        }
        else if ( speedyaw < -MAX_ABS_ANG_SPEED )
        {
            speedyaw = -MAX_ABS_ANG_SPEED;
        }
        
        // Calculate the PWM to output
        //F32 normalisedPWM = (speedyaw+MAX_ABS_ANG_SPEED)/(2.0f*MAX_ABS_ANG_SPEED);
        // or
        
        F32 normalisedPWM = (linearSpeed+MAX_ABS_LINEAR_SPEED)/(2.0f*MAX_ABS_LINEAR_SPEED);
      
        U32 pwmDuty = MIN_DUTY_CYCLE_US + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedPWM);
        
        U32 leftDuty = (U32)(1000 + (S32)((1000)*normalisedPWM));  // 1000 to 2000
        U32 rightDuty = (U32)(1200 + (S32)((600)*normalisedPWM));  // 1200 to 1800
        U32 frontDuty = (U32)(1700 + (S32)((-400)*normalisedPWM));  // 1700 to 1300
        U32 backDuty = (U32)(2000 + (S32)((-1000)*normalisedPWM));  // 2000 to 1000
        
        printf( "Setting PWMS %i, %i %i %i\n",
                leftDuty, rightDuty, frontDuty, backDuty );
        
        if ( mbInitialisedPWM )
        {
            pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, leftDuty );
            pwm_SetPulse( RIGHT_MOTOR_CHANNEL, PWM_FREQUENCY_US, rightDuty );
            pwm_SetPulse( FRONT_MOTOR_CHANNEL, PWM_FREQUENCY_US, frontDuty );
            pwm_SetPulse( BACK_MOTOR_CHANNEL, PWM_FREQUENCY_US, backDuty );
            /*if (speedyaw<0)
            {
                pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, pwmDuty );
                //pwm_SetPulse( RIGHT_MOTOR_CHANNEL, PWM_FREQUENCY_US, pwmDuty/2 );
                printf( "Turning right\n");
                printf( "Sending %i μs pulse\n", pwmDuty );
            }
            else
            {
                pwm_SetPulse( RIGHT_MOTOR_CHANNEL, PWM_FREQUENCY_US, pwmDuty );
                //pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, pwmDuty/2 );
                printf( "Turning left\n");
                printf( "Sending %i μs pulse\n", pwmDuty );
            }*/
            pwm_SetPulse( TEST_CHANNEL, PWM_FREQUENCY_US, pwmDuty );
        }
        
        

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
    else if ( Message::MatchMessage(
        pHeader, PLAYER_MSGTYPE_DATA, PLAYER_IMU_DATA_STATE, mCompassID ) )
    {
        player_imu_data_state_t* pCompassData = (player_imu_data_state_t*)pData;
        
        mYawCompassAngle = pCompassData->pose.pyaw;
        mPitchCompassAngle = pCompassData->pose.ppitch;
        
        mbCompassAngleValid = true;
        mCompassAngleTimestamp = pHeader->timestamp;
        
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
        
        if ( mbCompassAngleValid
            && mCompassAngleTimestamp != mLastDisplayedCompassAngleTimestamp )
        {
            // 0 < angle < 2*pi
            F32 radYawCompassAngle = mYawCompassAngle;
            while( radYawCompassAngle >= 2*M_PI)
            {
                radYawCompassAngle -= 2*M_PI;
            }
            
            F32 radPitchCompassAngle = mPitchCompassAngle;
            while( radPitchCompassAngle >= 2*M_PI)
            {
                radPitchCompassAngle -= 2*M_PI;
            }
            
            F32 degYawCompassAngle = radYawCompassAngle*180.0f/M_PI;
            F32 degPitchCompassAngle = radPitchCompassAngle*180.0f/M_PI;
            printf( "Current compass angle (degrees): yaw = %2.3f, pitch = %2.3f\n", degYawCompassAngle, degPitchCompassAngle );
            mLastDisplayedCompassAngleTimestamp = mCompassAngleTimestamp;
        }
    }
}

