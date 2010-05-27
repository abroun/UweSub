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
// Forward declarations
class UweSubInterface;

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

    private: static const U32 PWM_FREQUENCY_US;
    private: static const U32 MIN_DUTY_CYCLE_US;
    private: static const U32 MAX_DUTY_CYCLE_US;
    private: static const U32 ZERO_DUTY_CYCLE_US;
    
    private: static const U32 LEFT_MOTOR_CHANNEL;
    private: static const U32 TEST_CHANNEL;
    
    private: static const F32 MAX_ABS_FORWARD_SPEED;
    private: bool mbInitialisedPWM;
    
    // Used to keep track of the rate at which we update the interfaces
    protected: double mLastInterfaceUpdateTime;
};

//------------------------------------------------------------------------------
void MotorDriverRegister( DriverTable* pTable );

#endif // MOTOR_DRIVER_H
