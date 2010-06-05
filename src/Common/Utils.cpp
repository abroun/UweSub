//------------------------------------------------------------------------------
// File: Utils.h
// Desc: Common utility library for useful routines that have no other home
//
// Author: Alan Broun
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include "Utils.h"
#include <strings.h>
#include <time.h>

//------------------------------------------------------------------------------
S32 Utils::stricmp( const char* s1, const char* s2 )
{
    return strcasecmp( s1, s2 );
}

//------------------------------------------------------------------------------
void Utils::Sleep( HighPrecisionTime& time )
{
    timespec requestedTime;
    requestedTime.tv_sec = time.mSeconds;
    requestedTime.tv_nsec = time.mNanoSeconds;
    
    nanosleep( &requestedTime, NULL );
}