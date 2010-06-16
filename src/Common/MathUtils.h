//------------------------------------------------------------------------------
// File: MathUtils.h
// Desc: Hold all utility library that may need to be re-organised at some
//       point
//
// Author: Alan Broun
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#ifndef MATH_UTILS_H
#define MATH_UTILS_H

//------------------------------------------------------------------------------
#include <math.h>
#include "Common.h"

//------------------------------------------------------------------------------
class MathUtils
{
    //--------------------------------------------------------------------------
    public: static F32 RadToDeg( F32 radians ) 
    { 
        return radians * 180.0f / M_PI;
    }
    
    //--------------------------------------------------------------------------
    public: static F32 DegToRad( F32 degrees ) 
    { 
        return degrees * M_PI / 180.0f;
    }
    
    //--------------------------------------------------------------------------
    public: static F32 GradToRad( F32 grads )
    { 
        return grads * M_PI / 200.0f;
    }
};

#endif // MATH_UTILS_H
