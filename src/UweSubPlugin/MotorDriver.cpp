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
#define MOTOR_CONTROLLED 0
#define MOTOR_UNCONTROLLED 1

#define BIT_VALUE( x, bit ) ( (x >> bit) & 0x1 )

const U32 MotorDriver::PWM_FREQUENCY_US = 20000;
const U32 MotorDriver::MIN_DUTY_CYCLE_US = 1000;
const U32 MotorDriver::MAX_DUTY_CYCLE_US = 2000;
const U32 MotorDriver::ZERO_DUTY_CYCLE_US = (MIN_DUTY_CYCLE_US + MAX_DUTY_CYCLE_US)/2;

const U32 MotorDriver::RIGHT_MOTOR_CHANNEL = 3;    // 01
const U32 MotorDriver::LEFT_MOTOR_CHANNEL = 5;     // 10
const U32 MotorDriver::FRONT_MOTOR_CHANNEL = 4;     // Was 4
const U32 MotorDriver::BACK_MOTOR_CHANNEL = 2;      // Was 2
const U32 MotorDriver::TEST_CHANNEL = 16;

const F32 MotorDriver::MAX_ABS_2D_DIST = 1.0f;
const F32 MotorDriver::MAX_ABS_LINEAR_SPEED = 1.0f;
const F32 MotorDriver::MAX_ABS_ANG_SPEED = M_PI/6;

const F32 MOTOR_PER = 0.8;
const S32 LEFT_PWM_OFFSET = 0;
const S32 RIGHT_PWM_OFFSET = -20;
const S32 FRONT_PWM_OFFSET = 0;   // Was -20
const S32 BACK_PWM_OFFSET = -20;      // Was 0

//------------------------------------------------------------------------------
// Constructor.  Retrieve options from the configuration file and do any
// pre-Setup() setup.
MotorDriver::MotorDriver( ConfigFile* pConfigFile, int section )
    : ThreadedDriver( pConfigFile, section, false, 
        PLAYER_MSGQUEUE_DEFAULT_MAXLEN, PLAYER_POSITION3D_CODE ),
    mbCompassAvailable( false ),
    mLastDisplayedCompassAngleTimestamp( 0.0 ),
    mbDepthSensorAvailable( false ),
    mLastDisplayedDepthSensorDepthTimestamp( 0.0 ),
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
        pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US + LEFT_PWM_OFFSET );
        pwm_SetPulse( RIGHT_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US + RIGHT_PWM_OFFSET );
        pwm_SetPulse( FRONT_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US + FRONT_PWM_OFFSET );
        pwm_SetPulse( BACK_MOTOR_CHANNEL, PWM_FREQUENCY_US, ZERO_DUTY_CYCLE_US + BACK_PWM_OFFSET );
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
    
    mpDepthSensor = NULL;
    // See if we have a depth sensor
    if ( pConfigFile->ReadDeviceAddr( &mDepthSensorID, section, "requires",
                       PLAYER_POSITION1D_CODE, -1, NULL ) != 0 )
    {
        PLAYER_WARN( "No Depth Sensor specified" );
    }
    else
    {
        mbDepthSensorAvailable = true;
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
    
    if ( mbDepthSensorAvailable )
    {
        if ( Device::MatchDeviceAddress( mDepthSensorID, this->device_addr ) )
        {
            PLAYER_ERROR( "Attempting to subscribe to self" );
            return -1;
        }

        mpDepthSensor = deviceTable->GetDevice( mDepthSensorID );
        if ( NULL == mpDepthSensor )
        {
            PLAYER_ERROR( "Unable to locate suitable Depth Sensor device" );
            return -1;
        }

        if ( mpDepthSensor->Subscribe( this->InQueue ) != 0 )
        {
            PLAYER_ERROR( "Unable to subscribe to Depth Sensor device" );
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
        
       
        F32 depthSpeed = MOTOR_PER*MAX( -1.0f, MIN( (F32)pCmd->vel.pz, 1.0f ) );
        F32 normalisedFrontPWM = (depthSpeed + 1.0f)/2.0f;

        S32 frontDuty = MIN_DUTY_CYCLE_US 
            + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedFrontPWM);
        
        F32 PITCH_MOTER_PER = 0.5;
        F32 pitchSpeed = PITCH_MOTER_PER*MAX( -1.0f, MIN( (F32)pCmd->vel.ppitch, 1.0f ) );
        F32 normalisedBackPWM = (pitchSpeed + 1.0f)/2.0f;
        S32 backDuty = MIN_DUTY_CYCLE_US 
            + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedBackPWM);
            
        F32 linearSpeed = MAX( -1.0f, MIN( (F32)pCmd->vel.px, 1.0f ) );
        F32 yawSpeed = MAX( -1.0f, MIN( (F32)pCmd->vel.pyaw, 1.0f ) );
        F32 leftSpeed = MOTOR_PER*MAX( -1.0f, MIN( linearSpeed + yawSpeed, 1.0f ) );
        F32 rightSpeed = MOTOR_PER*MAX( -1.0f, MIN( linearSpeed - yawSpeed, 1.0f ) );
        
//         if ( yawSpeed > 0 )
//         {
//             F32 leftSpeed = MOTOR_PER*MAX( -1.0f, MIN( linearSpeed + yawSpeed, 1.0f ) );
//             F32 rightSpeed = MOTOR_PER*MAX( -1.0f, MIN( linearSpeed, 1.0f ) );       
//         }
//         else
//         {
//             F32 leftSpeed = MOTOR_PER*MAX( -1.0f, MIN( linearSpeed, 1.0f ) );
//             F32 rightSpeed = MOTOR_PER*MAX( -1.0f, MIN( linearSpeed - yawSpeed , 1.0f ) );
//         }   

        F32 normalisedLeftPWM = (leftSpeed + 1.0f)/2.0f;
        F32 normalisedRightPWM = (rightSpeed + 1.0f)/2.0f;
        S32 leftDuty = MIN_DUTY_CYCLE_US 
            + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedLeftPWM);
        S32 rightDuty = MIN_DUTY_CYCLE_US 
            + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedRightPWM);
        
        // Offset duty cycles to account for dodgy motor controllers
        leftDuty = MAX( MIN_DUTY_CYCLE_US, MIN( leftDuty + LEFT_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
        rightDuty = MAX( MIN_DUTY_CYCLE_US, MIN( rightDuty + RIGHT_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
        frontDuty = MAX( MIN_DUTY_CYCLE_US, MIN( frontDuty + FRONT_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
        backDuty = MAX( MIN_DUTY_CYCLE_US, MIN( backDuty + BACK_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
        
        //printf( "Depth speed: %2.3f, Pitch speed: %2.3f, yawSpeed %2.3f\n",
        //        depthSpeed, pitchSpeed, yawSpeed );
        
        //printf( "Seting PWMS %i, %i, %i, %i\n",
        //    leftDuty, rightDuty, frontDuty, backDuty );
        
        if ( mbInitialisedPWM )
        {
            U8 motorControlFlags = (S32)pCmd->state;
            
            if ( BIT_VALUE( motorControlFlags, 3 ) == MOTOR_CONTROLLED )
            {
                //printf( "Send L: %i ", leftDuty );
                pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, leftDuty );
            }
            if ( BIT_VALUE( motorControlFlags, 2 ) == MOTOR_CONTROLLED )
            {
                //printf( "Send R: %i ", rightDuty );
                pwm_SetPulse( RIGHT_MOTOR_CHANNEL, PWM_FREQUENCY_US, rightDuty );
            }
            if ( BIT_VALUE( motorControlFlags, 1 ) == MOTOR_CONTROLLED )
            {
                //printf( "Send F: %i ", frontDuty );
                pwm_SetPulse( FRONT_MOTOR_CHANNEL, PWM_FREQUENCY_US, frontDuty );
            }
            if ( BIT_VALUE( motorControlFlags, 0 ) == MOTOR_CONTROLLED )
            {
                //printf( "Send B: %i ", backDuty );
                pwm_SetPulse( BACK_MOTOR_CHANNEL, PWM_FREQUENCY_US, backDuty );
            }
            
            if ( 15 != motorControlFlags )
            {
                //printf( "\n" );
            }
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
        mRollCompassAngle = pCompassData->pose.proll;
        
        mbCompassAngleValid = true;
        mCompassAngleTimestamp = pHeader->timestamp;
        
        return 0;
    }
    else if ( Message::MatchMessage( pHeader, PLAYER_MSGTYPE_CMD, 
        PLAYER_POSITION3D_CMD_SET_POS, this->device_addr ) )
    {
        // AB: This is a complete abuse of the interface but basically
        // we use this message to set the motor powers directly. 
        // So, motor powers are place in the 'vel' component and are 
        // 'normalised' so -1.0 is full reverse and 1.0 is full forward.
        // Motors are
        // x = left
        // y = right
        // roll = forward
        // pitch = back
        // yaw = Motor control bits (0 == controlled, 1 == uncontrolled)
        
        player_position3d_cmd_pos_t* pCmd = (player_position3d_cmd_pos_t*)pData;

        F32 normalisedLeftPWM = -MOTOR_PER*MAX( -1.0f, MIN( (F32)pCmd->vel.px, 1.0f ) );
        F32 normalisedRightPWM = -MOTOR_PER*MAX( -1.0f, MIN( (F32)pCmd->vel.py, 1.0f ) );
        F32 normalisedFrontPWM = -MOTOR_PER*MAX( -1.0f, MIN( (F32)pCmd->vel.proll, 1.0f ) );
        F32 normalisedBackPWM = -MOTOR_PER*MAX( -1.0f, MIN( (F32)pCmd->vel.ppitch, 1.0f ) );
        
        normalisedLeftPWM = (normalisedLeftPWM + 1.0f)/2.0f;
        normalisedRightPWM = (normalisedRightPWM + 1.0f)/2.0f;
        normalisedFrontPWM = (normalisedFrontPWM + 1.0f)/2.0f;
        normalisedBackPWM = (normalisedBackPWM + 1.0f)/2.0f;
        
        S32 leftDuty = MIN_DUTY_CYCLE_US + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedLeftPWM);
        S32 rightDuty = MIN_DUTY_CYCLE_US + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedRightPWM);
        S32 frontDuty = MIN_DUTY_CYCLE_US + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedFrontPWM);
        S32 backDuty = MIN_DUTY_CYCLE_US + (U32)((MAX_DUTY_CYCLE_US-MIN_DUTY_CYCLE_US)*normalisedBackPWM);

        // Offset duty cycles to account for dodgy motor controllers
        leftDuty = MAX( MIN_DUTY_CYCLE_US, MIN( leftDuty + LEFT_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
        rightDuty = MAX( MIN_DUTY_CYCLE_US, MIN( rightDuty + RIGHT_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
        frontDuty = MAX( MIN_DUTY_CYCLE_US, MIN( frontDuty + FRONT_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
        backDuty = MAX( MIN_DUTY_CYCLE_US, MIN( backDuty + BACK_PWM_OFFSET, MAX_DUTY_CYCLE_US ) );
 
        printf( "Seting PWMS %i, %i, %i, %i\n",
            leftDuty, rightDuty, frontDuty, backDuty );
        
        if ( mbInitialisedPWM )
        {
            S32 motorControlFlags = (S32)pCmd->vel.pyaw;
            
            if ( BIT_VALUE( motorControlFlags, 3 ) == MOTOR_CONTROLLED )
            {
                pwm_SetPulse( LEFT_MOTOR_CHANNEL, PWM_FREQUENCY_US, leftDuty );
            }
            if ( BIT_VALUE( motorControlFlags, 2 ) == MOTOR_CONTROLLED )
            {
                pwm_SetPulse( RIGHT_MOTOR_CHANNEL, PWM_FREQUENCY_US, rightDuty );
            }
            if ( BIT_VALUE( motorControlFlags, 1 ) == MOTOR_CONTROLLED )
            {
                pwm_SetPulse( FRONT_MOTOR_CHANNEL, PWM_FREQUENCY_US, frontDuty );
            }
            if ( BIT_VALUE( motorControlFlags, 0 ) == MOTOR_CONTROLLED )
            {
                pwm_SetPulse( BACK_MOTOR_CHANNEL, PWM_FREQUENCY_US, backDuty );
            }
        }
        return 0;
    }
    else if ( Message::MatchMessage(
        pHeader, PLAYER_MSGTYPE_DATA, PLAYER_POSITION1D_DATA_STATE, mDepthSensorID ) )
    {
        player_position1d_data* pDepthSensorData = (player_position1d_data*)pData;
        mDepthSensorDepth = pDepthSensorData->pos;
           
        mbDepthSensorDepthValid = true;
        mDepthSensorDepthTimestamp = pHeader->timestamp;
        
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
            && mCompassAngleTimestamp != mLastDisplayedCompassAngleTimestamp
            && mbDepthSensorDepthValid
            && mDepthSensorDepthTimestamp != mLastDisplayedDepthSensorDepthTimestamp )
        {
            // 0 < angle < 2*pi
            F32 radCompassYawAngle = mYawCompassAngle;
            
            F32 radCompassPitchAngle = mPitchCompassAngle;
            while( radCompassPitchAngle >= 2*M_PI)
            {
                radCompassPitchAngle -= 2*M_PI;
            }
            
            F32 radCompassRollAngle = mRollCompassAngle;
            while( radCompassRollAngle >= 2*M_PI)
            {
                radCompassRollAngle -= 2*M_PI;
            }

            F32 degCompassYawAngle = radCompassYawAngle*180.0f/M_PI;
            F32 degCompassPitchAngle = radCompassPitchAngle*180.0f/M_PI;
            F32 degCompassRollAngle = radCompassRollAngle*180.0f/M_PI;
            F32 DepthSensorDepth = mDepthSensorDepth;
            
            printf( "Compass angle (degrees): yaw = %2.2f, pitch = %2.2f, roll = %2.2f | Sensor depth (m): %2.2f \n", degCompassYawAngle, degCompassPitchAngle, degCompassRollAngle, DepthSensorDepth );
            mLastDisplayedCompassAngleTimestamp = mCompassAngleTimestamp;
            mLastDisplayedDepthSensorDepthTimestamp = mDepthSensorDepthTimestamp;
        }
    }
}
