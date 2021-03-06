//------------------------------------------------------------------------------
// File: MotorDriver.h
// Desc: A driver for controlling the motors of the AUV using PWM signals
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>
#include "Common.h"

//------------------------------------------------------------------------------
class MotorDriver : public ThreadedDriver
{
    typedef ThreadedDriver base;
    
    // Constructor/Destructor
    public: MotorDriver( ConfigFile* pConfigFile, int section );
    public: virtual ~MotorDriver();

    // Set up the driver.  Return 0 if things go well, and -1 otherwise.
    public: virtual int MainSetup();

    // Shutdown the device
    public: virtual void MainQuit();

    // Process all messages for this driver. 
    public: virtual int ProcessMessage( QueuePointer& respQueue, 
                                        player_msghdr* pHeader, 
                                        void* pData );
                                        
    // The main routine of the thread
    private: virtual void Main();
    
    // Link to the compass device
    private: Device* mpCompass;
    private: player_devaddr_t mCompassID;
    private: bool mbCompassAvailable;
    
    private: F32 mYawCompassAngle;
    private: F32 mPitchCompassAngle;
    private: F32 mRollCompassAngle;
    private: bool mbCompassAngleValid;
    private: double mCompassAngleTimestamp;
    private: double mLastDisplayedCompassAngleTimestamp;
    
    // Link to the depth sensor device
    private: Device* mpDepthSensor;
    private: player_devaddr_t  mDepthSensorID;
    private: bool mbDepthSensorAvailable;
    
    private: F32 mDepthSensorDepth;
    private: bool mbDepthSensorDepthValid;
    private: double mDepthSensorDepthTimestamp;
    private: double mLastDisplayedDepthSensorDepthTimestamp;
    
    private: static const U32 PWM_FREQUENCY_US;
    private: static const U32 MIN_DUTY_CYCLE_US;
    private: static const U32 MAX_DUTY_CYCLE_US;
    private: static const U32 ZERO_DUTY_CYCLE_US;
    
    private: static const U32 LEFT_MOTOR_CHANNEL;
    private: static const U32 RIGHT_MOTOR_CHANNEL;
    private: static const U32 FRONT_MOTOR_CHANNEL;
    private: static const U32 BACK_MOTOR_CHANNEL;
    private: static const U32 TEST_CHANNEL;
    
    private: static const F32 MAX_ABS_2D_DIST;
    private: static const F32 MAX_ABS_LINEAR_SPEED;
    private: static const F32 MAX_ABS_ANG_SPEED;
    private: bool mbInitialisedPWM; 
};

//------------------------------------------------------------------------------
void MotorDriverRegister( DriverTable* pTable );

#endif // MOTOR_DRIVER_H
