//------------------------------------------------------------------------------
// File: Position3DInterface.h
// Desc: An interface that allows Player to move the AUV
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef POSITION_3D_INTERFACE_H
#define POSITION_3D_INTERFACE_H

//------------------------------------------------------------------------------
#include "UweSubInterface.h"

//------------------------------------------------------------------------------
class Position3DInterface : public UweSubInterface
{
    // Constructor
    public: Position3DInterface( player_devaddr_t addr, UweSubDriver* pDriver,
                              ConfigFile* pConfigFile, int section );
    // Destructor
    public: virtual ~Position3DInterface();

    // Handle all messages.
    public: virtual int ProcessMessage( QueuePointer &respQueue,
                                      player_msghdr_t* pHeader, void* pData );

    // Update this interface, publish new info.
    public: virtual void Update();
};

#endif // POSITION_3D_INTERFACE_H