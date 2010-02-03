#ifndef __PWM_H
#define __PWM_H

#include "defines.h"
#include "pwmdx.h"

#ifdef __cplusplus
extern "C" {
#endif

RBAPI(bool) pwm_InUse(void);

RBAPI(bool) pwm_Initialize(unsigned baseaddr, int clkmode, int irqmode);
//-- if the above function return false, ERR_Type may be settled as the following number:
//   #define ERROR_IOINITFAIL       (ERR_NOERROR + 100) //need include <io.h>
//   #define ERROR_IOSECTIONFULL    (ERR_NOERROR + 101) //need include <io.h>
//   #define ERROR_CPUUNSUPPORTED	(ERR_NOERROR + 102) //need include <io.h>
     #define ERROR_PWM_INUSE	    (ERR_NOERROR + 300)

RBAPI(void) pwm_Close(void);


RBAPI(void) pwm_SetBaseClock(int clock);
//-- values for the "clock" argument
//   #define PWMCLOCK_10MHZ    (0)
//   #define PWMCLOCK_50MHZ    (1)

RBAPI(bool) pwm_SetPulse(int channel, unsigned long period, unsigned long duty);		//resolution: 1us
RBAPI(bool) pwm_SetPulse_10MHZ(int channel, unsigned long period, unsigned long duty);	//resolution: 0.1us
RBAPI(bool) pwm_SetPulse_50MHZ(int channel, unsigned long period, unsigned long duty);	//resolution: 20ns
//-- if the above function return false, ERR_Type may be settled as the following number:
     #define ERROR_PWM_WRONGCHANNEL     (ERR_NOERROR + 310)
     #define ERROR_PWM_INVALIDPULSE     (ERR_NOERROR + 311)
     #define ERROR_PWM_CLOCKMISMATCH    (ERR_NOERROR + 312)


/*
void pwm_BackupAllSettings(void);
void pwm_RestoreAllSettings(void);
*/

#ifdef __cplusplus
}
#endif

#endif

