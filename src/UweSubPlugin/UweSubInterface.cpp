//------------------------------------------------------------------------------
// File: UweSubInterface.h
// Desc: Generic UweSub device inteface for Player
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include "UweSubInterface.h"
#include "UweSubDriver.h"

//------------------------------------------------------------------------------
UweSubInterface::UweSubInterface( player_devaddr_t addr, UweSubDriver* pDriver,
                                 ConfigFile* /* pConfigFile */, int /*section*/ )
{
    mDeviceAddress = addr;
    mpDriver = pDriver;
}

//------------------------------------------------------------------------------
UweSubInterface::~UweSubInterface()
{
}

