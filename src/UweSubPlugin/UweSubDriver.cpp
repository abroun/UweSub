//------------------------------------------------------------------------------
// File: UweSubDriver.cpp
// Desc: A driver for Player so that it can control the UWE AUV
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <stdio.h>
#include "UweSubDriver.h"
#include "Position3DInterface.h"

//------------------------------------------------------------------------------
// A factory creation function, declared outside of the class so that it
// can be invoked without any object context (alternatively, you can
// declare it static in the class).  In this function, we create and return
// (as a generic Driver*) a pointer to a new instance of this driver.
Driver* UweSubDriverInit( ConfigFile* pConfigFile, int section )
{
    // Create and return a new instance of this driver
    return (Driver*)(new UweSubDriver( pConfigFile, section ));
}

//------------------------------------------------------------------------------
// A driver registration function, again declared outside of the class so
// that it can be invoked without object context.  In this function, we add
// the driver into the given driver table, indicating which interfaces the
// driver can support and how to create a driver instance.
void UweSubDriverRegister( DriverTable* pTable )
{
    if ( !player_quiet_startup )
    {
        printf( "\n ** UweSub plugin **\n" );

        //printf("\n * Part of the Player/Stage Project [http://playerstage.sourceforge.net]\n"
        //    " * Copyright 2000-2006 Richard Vaughan, Andrew Howard, Brian Gerkey, Nathan Koenig\n"
        //    " * and contributors. Released under the GNU General Public License v2.");
    }

    pTable->AddDriver( (char*)"uwesub", UweSubDriverInit );
}

//------------------------------------------------------------------------------
// Need the extern to avoid C++ name-mangling
extern "C"
{
    int player_driver_init( DriverTable* pTable )
    {
        UweSubDriverRegister( pTable );
        return 0;
    }
}

//------------------------------------------------------------------------------
// UweSubDriver
//------------------------------------------------------------------------------
static const double SDD_INTERFACE_UPDATES_PER_SECOND = 30.0;
static const int SDD_NUM_MESSAGES_HANDLED_PER_UPDATE = -1;

//------------------------------------------------------------------------------
// Constructor.  Retrieve options from the configuration file and do any
// pre-Setup() setup.
UweSubDriver::UweSubDriver( ConfigFile* pConfigFile, int section )
    : Driver( pConfigFile, section, false, 4096 ),
    mpDeviceList( NULL ),
    mNumDevices( 0 ),
    mMaxNumDevices( 0 )
{
    this->alwayson = true;
    //mLastInterfaceUpdateTime = mSim.GetSimTime();
    if ( LoadDevices( pConfigFile, section ) < 0 )
    {
        fprintf( stderr, "Error: Unable load devices\n" );
    }
}

//------------------------------------------------------------------------------
UweSubDriver::~UweSubDriver()
{
}

//------------------------------------------------------------------------------
// Set up the device.  Return 0 if things go well, and -1 otherwise.
int UweSubDriver::Setup()
{
    return 0;
}


//------------------------------------------------------------------------------
// Shutdown the device
int UweSubDriver::Shutdown()
{
    return 0;
}

//------------------------------------------------------------------------------
// Process all messages for this driver.
int UweSubDriver::ProcessMessage( QueuePointer& respQueue,
                                player_msghdr* pHeader, void* pData )
{   
    // Find the right device interface to handle this config
    UweSubInterface* pDeviceInterface = LookupDevice( pHeader->addr );

    if ( NULL != pDeviceInterface )
    {
        return( pDeviceInterface->ProcessMessage( respQueue, pHeader, pData ) );
    }
    else
    {
        fprintf( stderr, "Error: Can't find interface for device %d.%d.%d",
            pHeader->addr.robot,
            pHeader->addr.interf,
            pHeader->addr.index );
        return -1;
    }
}

//------------------------------------------------------------------------------
// Subscribe to a device using a message queue
int UweSubDriver::Subscribe( QueuePointer& respQueue, player_devaddr_t addr )
{
    UweSubInterface* pDeviceInterface = this->LookupDevice( addr );

    if( pDeviceInterface )
    {
        pDeviceInterface->Subscribe();
        pDeviceInterface->Subscribe( respQueue );
        return Driver::Subscribe( addr );
    }

    fprintf( stderr, "Error: Unable to find device\n" );
    return 1; // error
}

//------------------------------------------------------------------------------
// Unsubscribe to a device using a message queue
int UweSubDriver::Unsubscribe( QueuePointer& respQueue, player_devaddr_t addr )
{
    UweSubInterface* pDeviceInterface = this->LookupDevice( addr );

    if( pDeviceInterface )
    {
        pDeviceInterface->Unsubscribe();
        pDeviceInterface->Unsubscribe( respQueue );
        return Driver::Unsubscribe( addr );
    }

    fprintf( stderr, "Error: Unable to find device\n" );
    return 1; // error
}

//------------------------------------------------------------------------------
// Main function for device thread
void UweSubDriver::Update()
{
    Driver::ProcessMessages( SDD_NUM_MESSAGES_HANDLED_PER_UPDATE );
    
    // Check to see if we should update the interfaces
    /*double simTime = mSim.GetSimTime();
    if ( simTime - mLastInterfaceUpdateTime 
        >= 1.0/SDD_INTERFACE_UPDATES_PER_SECOND )
    {*/
        for ( int deviceIdx = 0; deviceIdx < mNumDevices; deviceIdx++ )
        {
            UweSubInterface* pDeviceInterface = mpDeviceList[ deviceIdx ];
            pDeviceInterface->Update();
        }
        
    /*    mLastInterfaceUpdateTime = simTime;
    }*/
    
    // Check to see if the simulation is still running
    /*if ( mSim.IsRunning() )
    {
        mSim.Update();
    }
    else
    {
        // Rather abrupt, but this seems to be what Stage does...
        exit( 0 );
    }*/

    return;
}

//------------------------------------------------------------------------------
// Helper function to load all devices on startup
int UweSubDriver::LoadDevices( ConfigFile* pConfigFile, int section )
{
    // Get the device count, and create the device array
    mMaxNumDevices = pConfigFile->GetTupleCount( section, "provides" );
    mpDeviceList = (UweSubInterface**)realloc( mpDeviceList, 
        mMaxNumDevices * sizeof( UweSubInterface* ) );

    if ( !player_quiet_startup )
    {
        printf( "  UweSub Plugin driver creating %d %s\n",
            mMaxNumDevices,
            mMaxNumDevices == 1 ? "device" : "devices" );
    }

    // Load all the devices
    for ( int deviceIdx = 0; deviceIdx < mMaxNumDevices; deviceIdx++ )
    {
        player_devaddr_t playerAddr;

        // Read in the Device address
        if ( pConfigFile->ReadDeviceAddr( &playerAddr, section,
                            "provides", 0, deviceIdx, NULL ) != 0 )
        {
            SetError( -1 );
            return -1;
        }

        if ( !player_quiet_startup )
        {
            printf( "    %d.%s.%d is",
                playerAddr.robot, 
                interf_to_str( playerAddr.interf ),
                playerAddr.index );
            fflush(stdout);
        }

        UweSubInterface* pDeviceInterface = NULL;

        switch ( playerAddr.interf )
        {
        case PLAYER_POSITION3D_CODE:
            {
                if ( !player_quiet_startup ) printf( " a position3d interface.\n" );
                pDeviceInterface = new Position3DInterface( playerAddr, this, pConfigFile, section );
                break;
            }
        default:
            {
                fprintf( stderr, "Error: UweSub driver doesn't support interface type %d\n",
                    playerAddr.interf );
                SetError( -1 );
                return -1;
            }
        }

        if ( NULL != pDeviceInterface )
        {
            // Attempt to add this interface and we're done
            if ( AddInterface( pDeviceInterface->mDeviceAddress ) != 0 )
            {
                printf( "UweSub driver error: AddInterface() failed\n" );
                SetError( -2 );
                return -1;
            }

            // Store the interface in our device list
            mpDeviceList[ mNumDevices++ ] = pDeviceInterface;
        }
        else
        {
            fprintf( stderr, "Error: No UweSub source found for interface %d:%d:%d",
                playerAddr.robot,
                playerAddr.interf,
                playerAddr.index );

            SetError( -3 );
            return -1;
        }
    }

    return 0;
}

//------------------------------------------------------------------------------
// Find a device according to a player_devaddr
UweSubInterface* UweSubDriver::LookupDevice( player_devaddr_t addr )
{
    UweSubInterface* pResult = NULL;

    for ( int deviceIdx = 0; deviceIdx < mNumDevices; deviceIdx++ )
    {
        UweSubInterface* pTestInterface = (UweSubInterface*)mpDeviceList[ deviceIdx ];

        if ( pTestInterface->mDeviceAddress.robot == addr.robot 
            && pTestInterface->mDeviceAddress.interf == addr.interf 
            && pTestInterface->mDeviceAddress.index == addr.index )
        {
            // We've found the device
            pResult = pTestInterface;
            break;
        }
    }

    return pResult;
}
