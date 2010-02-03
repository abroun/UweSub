//------------------------------------------------------------------------------
// File: UweSubDriver.h
// Desc: A driver for Player so that it can control the UWE AUV
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef UWE_SUB_DRIVER_H
#define UWE_SUB_DRIVER_H

//------------------------------------------------------------------------------
#include <libplayercore/playercore.h>

//------------------------------------------------------------------------------
// Forward declarations
class UweSubInterface;

//------------------------------------------------------------------------------
class UweSubDriver : public Driver
{
    // Constructor/Destructor
    public: UweSubDriver( ConfigFile* pConfigFile, int section );
    public: virtual ~UweSubDriver();

    // Set up the device.  Return 0 if things go well, and -1 otherwise.
    public: virtual int Setup();

    // Shutdown the device
    public: virtual int Shutdown();

    // Process all messages for this driver. 
    public: virtual int ProcessMessage( QueuePointer& respQueue, 
                                        player_msghdr* pHeader, 
                                        void* pData );
                                        
    public: virtual int Subscribe( QueuePointer& respQueue, player_devaddr_t addr );
    public: virtual int Unsubscribe( QueuePointer& respQueue, player_devaddr_t addr );

    // The server thread calls this method frequently. We use it 
    // to check  for new commands and configs
    private: virtual void Update();

    // Helper function to load all devices on startup
    private: int LoadDevices( ConfigFile* pConfigFile, int section );

    // Find a device according to a player_devaddr
    private: UweSubInterface* LookupDevice( player_devaddr_t addr );

    // Array of interfaces associated with this driver
    protected: UweSubInterface** mpDeviceList;

    // Number of devices
    protected: int mNumDevices;

    // Max device count
    protected: int mMaxNumDevices;
    
    // Used to keep track of the rate at which we update the interfaces
    protected: double mLastInterfaceUpdateTime;
};

#endif // UWE_SUB_DRIVER_H
