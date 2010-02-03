#ifndef __SPI_H
#define __SPI_H

#include "defines.h"
#include "spidx.h"


#ifdef __cplusplus
extern "C" {
#endif

RBAPI(bool) spi_InUse(void);

//note: SPI lib assumes that I/O pins for GPIO3/SPI have functioned as GPIO3 or SPI pins;
//      this is BIOS default setting in general.
RBAPI(bool) spi_Initialize(int clkmode);
//-- values for the "clkmode" argument
     #define SPICLK_21400KHZ    (0)
     #define SPICLK_18750KHZ    (1)
     #define SPICLK_15000KHZ    (2)
     #define SPICLK_12500KHZ    (3)
     #define SPICLK_10000KHZ    (4)
     #define SPICLK_10714KHZ    (5)
     #define SPICLK_11538KHZ    (6)
     #define SPICLK_13636KHZ    (7)
     #define SPICLK_16666KHZ    (8)
     #define SPICLK_25000KHZ    (9)
     #define SPICLK_30000KHZ    (10)
     #define SPICLK_37000KHZ    (11)
     #define SPICLK_50000KHZ    (12)
     #define SPICLK_75000KHZ    (13)
     #define SPICLK_150000KHZ   (14)
//-- if the above function return false, ERR_Type may be settled as the following number:
//   #define ERROR_IOINITFAIL       (ERR_NOERROR + 100) //need include <io.h>
//   #define ERROR_IOSECTIONFULL    (ERR_NOERROR + 101) //need include <io.h>
//   #define ERROR_CPUUNSUPPORTED	(ERR_NOERROR + 102) //need include <io.h>
     #define ERROR_SPI_INUSE		(ERR_NOERROR + 200)
     #define ERROR_SPI_INITFAIL		(ERR_NOERROR + 202)

RBAPI(void) spi_Close(void);

RBAPI(bool) spi_EnableSS(void);
RBAPI(bool) spi_DisableSS(void);
//-- if the above functions return false, ERR_Type may be settled as the following number:
//   #define ERROR_SPIFIFOFAIL      (ERR_NOERROR + 215)

#ifdef __cplusplus
}
#endif

#endif

