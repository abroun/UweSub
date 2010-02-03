//------------------------------------------------------------------------------
// File: UweSubInterface.h
// Desc: Generic UweSub device inteface for Player
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef UWE_SUB_INTERFACE_H
#define UWE_SUB_INTERFACE_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>

//------------------------------------------------------------------------------
// Forward declarations
class UweSubDriver;

//------------------------------------------------------------------------------
// Base class for all the Player interfaces
class UweSubInterface
{
    // Constructor
    public: UweSubInterface( player_devaddr_t addr, UweSubDriver* pDriver, 
        ConfigFile* pConfigFile, int section );

    // Destructor
    public: virtual ~UweSubInterface();

    //  Handle all messages.
    public: virtual int ProcessMessage( QueuePointer &respQueue,
                                     player_msghdr_t* pHeader, void* pData ) = 0;

    public: virtual void Subscribe() {};
    public: virtual void Unsubscribe() {};
    public: virtual void Subscribe( QueuePointer& respQueue ) {}; 
    public: virtual void Unsubscribe( QueuePointer& respQueue ) {};
                                     
    // Update this interface, publish new info.
    public: virtual void Update() = 0;

    // Address of the Player Device
    public: player_devaddr_t mDeviceAddress;

    // Driver instance that created this device
    public: UweSubDriver* mpDriver;
};

#endif // UWE_SUB_INTERFACE_H
