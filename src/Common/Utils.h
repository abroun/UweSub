//------------------------------------------------------------------------------
// File: Utils.h
// Desc: Common utility library for useful routines that have no other home
//
// Author: Alan Broun
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef UTILS_H
#define UTILS_H

//------------------------------------------------------------------------------
#include "Common.h"
#include "Common/HighPrecisionTime.h"

//------------------------------------------------------------------------------
class Utils
{
    //--------------------------------------------------------------------------
    // Apparently Linux does not have stricmp so we provide a cross platform
    // alternative
    public: static S32 stricmp( const char* s1, const char* s2 );
    
    //--------------------------------------------------------------------------
    // Attempt at a cross platform 'nanosleep'
    public: static void Sleep( HighPrecisionTime& time );
};

#endif // UTILS_H
