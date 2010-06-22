//------------------------------------------------------------------------------
// File: UweSubPlugin.cpp
// Desc: A plug-in for Player that provides a number of drivers for controlling
// the UWE AUV
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include "CompassDriver.h"
#include "DepthSensorDriver.h"
#include "MotorDriver.h"
#include "SonarDriver.h"
#include "PingerDriver.h"

//------------------------------------------------------------------------------
// Need the extern to avoid C++ name-mangling
extern "C"
{
    int player_driver_init( DriverTable* pTable )
    {
        CompassDriverRegister( pTable );
        DepthSensorDriverRegister( pTable );
        MotorDriverRegister( pTable );
        SonarDriverRegister( pTable );
        PingerDriverRegister( pTable );
        return 0;
    }
}

