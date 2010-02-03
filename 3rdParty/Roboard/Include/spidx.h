#ifndef __SPIDX_H
#define __SPIDX_H

#include "defines.h"


#ifdef __cplusplus
extern "C" {
#endif

RBAPI(void) spi_SetBaseAddress(unsigned baseaddr);
RBAPI(unsigned) spi_SetDefaultBaseAddress(void);

RBAPI(bool) spi_SetControlREG(unsigned char ctrlreg);
//-- if the above function return false, ERR_Type may be settled as the following number:
     #define ERROR_SPIBUSY           (ERR_NOERROR + 210)

RBAPI(void) spi_SetErrorREG(unsigned char errreg);

RBAPI(unsigned char) spi_ReadControlREG(void);
RBAPI(unsigned char) spi_ReadStatusREG(void);
RBAPI(unsigned char) spi_ReadCSREG(void);
RBAPI(unsigned char) spi_ReadErrorREG(void);

RBAPI(bool) spi_EnableFIFO(void);
RBAPI(bool) spi_DisableFIFO(void);
RBAPI(bool) spi_SetClockDivisor(unsigned char clkdiv);
//-- if the above function return false, ERR_Type may be settled as the following number:
     #define ERROR_SPIWRONGCLOCK     (ERR_NOERROR + 211)


RBAPI(bool) spi_InputReady(void);
RBAPI(bool) spi_OutputFIFOEmpty(void);
RBAPI(bool) spi_OutputFIFOFull(void);
RBAPI(bool) spi_Busy(void);

RBAPI(bool) spierror_SPIBusy(void);
RBAPI(bool) spierror_InputOverlap(void);
RBAPI(bool) spierror_FIFOUnderrun(void);
RBAPI(bool) spierror_FIFOOverrun(void);

RBAPI(void) spierror_ClearSPIBusy(void);
RBAPI(void) spierror_ClearInputOverlap(void);
RBAPI(void) spierror_ClearFIFOUnderrun(void);
RBAPI(void) spierror_ClearFIFOOverrun(void);
RBAPI(void) spi_ClearErrors(void);


RBAPI(bool) spi_Write(unsigned char val);
RBAPI(bool) spi_WriteFlush(unsigned char val);
//-- if the above functions return false, ERR_Type may be settled as the following number:
     #define ERROR_SPIFIFOFULL      (ERR_NOERROR + 214)
     #define ERROR_SPIFIFOFAIL      (ERR_NOERROR + 215)

RBAPI(bool) spi_FIFOFlush(void);
//-- if the above functions return false, ERR_Type may be settled as the following number:
//   #define ERROR_SPIFIFOFAIL      (ERR_NOERROR + 215)

RBAPI(unsigned) spi_Read(void);
//-- if the above function return 0xffff, ERR_Type may be settled as the following number:
//   #define ERROR_SPIFIFOFAIL      (ERR_NOERROR + 215)
     #define ERROR_SPIREADFAIL      (ERR_NOERROR + 219)

RBAPI(unsigned) spi_Read2(void);
RBAPI(unsigned) spi_ReadStrict(void); //avoid to read overdue data in SPI input buffer
//-- if the above function return 0xffff, ERR_Type may be settled as the following number:
//   #define ERROR_SPIREADFAIL      (ERR_NOERROR + 219)

#ifdef __cplusplus
}
#endif

#endif

