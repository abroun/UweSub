#ifndef __DEFINES_H
#define __DEFINES_H

#if defined(__BORLANDC__) && (__BORLANDC__ == 0x0410)
    #define BC30

    typedef int bool;
    #define true  (1==1)
    #define false (1==0)
    
    #define __FUNCTION__    ("XXXXXXXX")
#endif


#if defined __cplusplus
    #define _RB_INLINE  inline
#elif defined(__GNUC__) //|| defined(DJGPP)
    #define _RB_INLINE  __inline__
#elif defined(_MSC_VER)
    #define _RB_INLINE  __inline
#else
    #define _RB_INLINE  static
#endif


#if defined(WIN32) || defined(WINCE)
    //#define ROBOIO_DLL
	//#define DLL_EXPORTING
#endif

#ifdef ROBOIO_DLL
    #ifdef DLL_EXPORTING
        #define RBAPI(rtype)    __declspec(dllexport) rtype __stdcall
        #define _RBAPI_C(rtype) __declspec(dllexport) rtype __cdecl
    #else
        #define RBAPI(rtype)    __declspec(dllimport) rtype __stdcall
        #define _RBAPI_C(rtype) __declspec(dllimport) rtype __cdecl
    #endif
    
    #define RB_INLINE
#else
    #define RBAPI(rtype)    rtype
    #define _RBAPI_C(rtype) rtype
    #define RB_INLINE       _RB_INLINE
#endif //ROBOIO_DLL

#endif

