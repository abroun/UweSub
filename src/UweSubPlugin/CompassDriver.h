//------------------------------------------------------------------------------
// File: CompassDriver.h
// Desc: A driver for controlling a PNI Compass
//
// Usage Example:
//
//  driver
//  (
//    name "compassdriver"
//    provides ["imu:0"]
//    requires ["opaque:0"]
//    buffer_size 20480
//  )
//
//  driver
//  (
//    name "serialstream"
//    provides ["opaque:0"]
//    port "/dev/ttyS0"
//  )
//
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef COMPASS_DRIVER_H
#define COMPASS_DRIVER_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>
#include "Common.h"
#include "Common/HighPrecisionTime.h"
#include "DataStructures/RollingBuffer.h"

//------------------------------------------------------------------------------
enum eCompassCommand
{
    eCC_None = 0,          // Set when we're not expecting a response
    eCC_GetModInfo,        // Queries the modules type and firmware revision number.
    eCC_ModInfoResp,       // Response to kGetModInfo
    eCC_SetDataComponents, // Sets the data components to be output.
    eCC_GetData,           // Queries the module for data
    eCC_DataResp,          // Response to kGetData
    eCC_SetConfig,         // Sets internal configurations in the module
    eCC_GetConfig,         // Queries the module for the current internal configuration value
    eCC_ConfigResp,        // Response to kGetConfig
    eCC_Save,              // Commands the module to save internal and user calibration
    eCC_StartCal,          // Commands the module to start user calibration
    eCC_StopCal,           // Commands the module to stop user calibration
    eCC_SetParam,          // Sets the FIR filter settings for the magnetometer & accelerometer
                            // sensors.
    eCC_GetParam,          // Queries for the FIR filter settings for the magnetometer &
                            // accelerometer sensors.
    eCC_ParamResp,         // Contains the FIR filter settings for the magnetometer &
                            // accelerometer sensors.
    eCC_PowerDown,         // Used to completely power-down the module
    eCC_SaveDone,          // Response to kSave
    eCC_UserCalSampCount,  // Sent from the module after taking a calibration sample point
    eCC_UserCalScore,      // Contains the calibration score
    eCC_SetConfigDone,     // Response to kSetConfig
    eCC_SetParamDone,      // Response to kSetParam
    eCC_StartIntervalMode, // Commands the module to output data at a fixed interval
    eCC_StopIntervalMode,  // Commands the module to stop data output at a fixed interval
    eCC_PowerUp,           // Sent after wake up from power down mode
    eCC_SetAcqParams,      // Sets the sensor acquisition parameters
    eCC_GetAcqParams,      // Queries for the sensor acquisition parameters
    eCC_AcqParamsDone,     // Response to kSetAcqParams
    eCC_AcqParamsResp,     // Response to kGetAcqParams
    eCC_PowerDownDone,     // Response to kPowerDown
    eCC_FactoryUserCal,    // Clears user calibration coefficients
    eCC_FactorUserCalDone, // Response to kFactoryUserCal
    eCC_TakeUserCalSample, // Commands the unit to take a sample during user calibration
    eCC_NumCommands
};

enum eCompassDataComponent
{
    eCDC_HeadingDegrees = 5,
    eCDC_TemperatureCelsius = 7,
    eCDC_Distortion = 8,
    eCDC_Calibrated = 9,
    eCDC_PitchCalibratedG = 21,
    eCDC_RollCalibratedG = 22,
    eCDC_IZ_CalibratedG = 23,
    eCDC_PitchDegrees = 24,
    eCDC_RollDegrees = 25,
    eCDC_AlignedMagneticX = 27,
    eCDC_AlignedMagneticY = 28,
    eCDC_AlignedMagneticZ = 29
};

//------------------------------------------------------------------------------
// TODO: We might want to put in bools to say whether fields are valid or not.
// For now we just set invalid fields to 0
struct CompassData
{
    F32 mHeadingDegrees;
    F32 mTemperatureCelsius;
    bool mbDistortion;
    bool mbCalibrated;
    F32 mPitchCalibratedG;
    F32 mRollCalibratedG;
    F32 mIZ_CalibratedG;
    F32 mPitchDegrees;
    F32 mRollDegrees;
    F32 mAlignedMagneticX;
    F32 mAlignedMagneticY;
    F32 mAlignedMagneticZ;
};

//------------------------------------------------------------------------------
class CompassDriver : public ThreadedDriver
{
    typedef ThreadedDriver base;
    
    // Constructor/Destructor
    public: CompassDriver( ConfigFile* pConfigFile, int section );
    public: virtual ~CompassDriver();

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
    
    private: void ProcessData();
    
    private: void SendGetModInfoCommand();
    private: void SendGetDataCommand();
    private: void SendCommandDataBuffer( void* pData, S32 numBytes, eCompassCommand expectedResponse = eCC_None );
    
    private: void ExtractDataFromPacket( U8* pPacketBuffer, S32 numBytes, CompassData* pCompassDataOut );
    
    // Helper routine that calcuates the CRC value for a block of data
    private: U16 CalculateCRC( U8* pData, U32 numBytes );

    // Properties
    private: IntProperty mBufferSize;
    
    // Link to the communication stream
    private: Device* mpOpaque;
    private: player_devaddr_t mOpaqueID;
    
    private: RollingBuffer mBuffer;
    
    private: static const U32 DEFAULT_BUFFER_SIZE;
    private: static const S32 COMPASS_COMMAND_ID_PACKET_IDX;
    private: static const F32 COMPASS_WAIT_TIME;
    
    private: enum eState
    {
        eS_Invalid,
        eS_GettingModInfo,
        eS_PollingForData,
        eS_NumStates
    };
    
    private: eState mState;
    private: eCompassCommand mExpectedResponse;
    private: bool mbWaitingForCompass;
    private: HighPrecisionTime mWaitStartTime;
};

//------------------------------------------------------------------------------
void CompassDriverRegister( DriverTable* pTable );

#endif // COMPASS_DRIVER_H
