#ifndef __AD79X8_H
#define __AD79X8_H

#include "defines.h"


#ifdef __cplusplus
extern "C" {
#endif

#define AD79x8_READFAIL (0x7fff)
#define AD7908_READFAIL (AD79x8_READFAIL)
#define AD7918_READFAIL (AD79x8_READFAIL)
#define AD7928_READFAIL (AD79x8_READFAIL)


//Raw ADC Read/Write Functions:
RBAPI(unsigned) ad79x8_RawRead(void);
//-- if the above function return AD79x8_READFAIL, ERR_Type may be settled as the following number:
     #define ERROR_ADCFAIL           (ERR_NOERROR + 310)

RBAPI(bool) ad79x8_RawWrite(unsigned val);
RBAPI(bool) ad7908_WriteCTRLREG(unsigned ctrlreg);
//-- if the above functions return false, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)


RBAPI(bool) ad79x8_InUse(void);

RBAPI(bool) ad79x8_Initialize(int channel, int range, int coding);
//-- values for the "range" augment
     #define AD79x8MODE_RANGE_VREF         (0)
     #define AD79x8MODE_RANGE_2VREF        (1)
//-- values for the "coding" augment
     #define AD79x8MODE_CODING_UNSIGNED    (0)
     #define AD79x8MODE_CODING_SIGNED      (1)
//-- if the above function return false, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)
     #define ERROR_ADC_NOSPI		 (ERR_NOERROR + 331)
     #define ERROR_ADC_INUSE         (ERR_NOERROR + 332)
     #define ERROR_ADC_WRONGCHANNEL  (ERR_NOERROR + 311)

RBAPI(bool) ad79x8_Close(void);
//-- if the above function return false, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)

RBAPI(bool) ad79x8_ChangeChannel(int channel, int range, int coding);
//-- if the above function return false, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)
//   #define ERROR_ADC_WRONGCHANNEL  (ERR_NOERROR + 311)


RBAPI(bool) ad79x8_InitializeMCH(unsigned char usedchannels, int range, int coding);
//-- values for the "usedchannels" argument of the above functions (note that
//   different values can be added to apply multiple channels)
     #define AD79x8_USECHANNEL0	     (1<<7)
     #define AD79x8_USECHANNEL1		 (1<<6)
     #define AD79x8_USECHANNEL2	     (1<<5)
     #define AD79x8_USECHANNEL3		 (1<<4)
     #define AD79x8_USECHANNEL4	     (1<<3)
     #define AD79x8_USECHANNEL5      (1<<2)
     #define AD79x8_USECHANNEL6      (1<<1)
     #define AD79x8_USECHANNEL7      (1<<0)
//-- if the above function return false, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)
//   #define ERROR_ADC_NOSPI		 (ERR_NOERROR + 331)
//   #define ERROR_ADC_INUSE         (ERR_NOERROR + 332)

RBAPI(bool) ad79x8_ChangeChannels(unsigned char usedchannels, int range, int coding);
//-- values for the "usedchannels" argument of the above functions (note that
//   different values can be added to apply multiple channels)
//   #define AD79x8_USECHANNEL0	     (1<<7)
//   #define AD79x8_USECHANNEL1		 (1<<6)
//   #define AD79x8_USECHANNEL2	     (1<<5)
//   #define AD79x8_USECHANNEL3		 (1<<4)
//   #define AD79x8_USECHANNEL4	     (1<<3)
//   #define AD79x8_USECHANNEL5      (1<<2)
//   #define AD79x8_USECHANNEL6      (1<<1)
//   #define AD79x8_USECHANNEL7      (1<<0)
//-- if the above function return false, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)



/*******************************  AD7908  *********************************/

//AD7908 Channel-by-Channel Reading Function:
//--------------------------------------------
RBAPI(int) ad7908_ReadChannel(int channel, int range, int coding);  //don't use in batch mode
//-- if the above function return AD7908_READFAIL, ERR_Type may be settled as the following number:
//   #define ERROR_ADC_NOSPI		 (ERR_NOERROR + 331)
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)


//AD7908 Single-Channel Batch Mode Functions:
//--------------------------------------------
#define ad7908_InUse                  ad79x8_InUse

#define ad7908_Initialize             ad79x8_Initialize
//-- values for the "range" augment
     #define AD7908MODE_RANGE_VREF    (AD79x8MODE_RANGE_VREF)
     #define AD7908MODE_RANGE_2VREF   (AD79x8MODE_RANGE_2VREF)
//-- values for the "coding" augment
     #define AD7908MODE_CODING_255    (AD79x8MODE_CODING_UNSIGNED)
     #define AD7908MODE_CODING_127    (AD79x8MODE_CODING_SIGNED)

#define ad7908_Close                  ad79x8_Close

#define ad7908_ChangeChannel          ad79x8_ChangeChannel

RBAPI(int) ad7908_Read(void);
//-- if the above function return AD7908_READFAIL, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL            (ERR_NOERROR + 310)


//AD7908 Multi-Channels Batch Mode Functions:
//--------------------------------------------
#define ad7908_InitializeMCH          ad79x8_InitializeMCH
//-- values for the "usedchannels" argument of the above functions
     #define AD7908_USECHANNEL0	      (AD79x8_USECHANNEL0)
     #define AD7908_USECHANNEL1		  (AD79x8_USECHANNEL1)
     #define AD7908_USECHANNEL2	      (AD79x8_USECHANNEL2)
     #define AD7908_USECHANNEL3		  (AD79x8_USECHANNEL3)
     #define AD7908_USECHANNEL4	      (AD79x8_USECHANNEL4)
     #define AD7908_USECHANNEL5       (AD79x8_USECHANNEL5)
     #define AD7908_USECHANNEL6       (AD79x8_USECHANNEL6)
     #define AD7908_USECHANNEL7       (AD79x8_USECHANNEL7)

#define ad7908_CloseMCH               ad79x8_Close

#define ad7908_ChangeChannels         ad79x8_ChangeChannels

RBAPI(int*) ad7908_ReadMCH(void);
/*---------------------------  end of AD7908  ----------------------------*/



/*******************************  AD7918  *********************************/

//AD7918 Channel-by-Channel Reading Function:
//--------------------------------------------
RBAPI(int) ad7918_ReadChannel(int channel, int range, int coding);  //don't use in batch mode
//-- if the above function return AD7918_READFAIL, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)
//   #define ERROR_ADC_NOSPI		 (ERR_NOERROR + 331)


//AD7918 Single-Channel Batch Mode Functions:
//--------------------------------------------
#define ad7918_InUse                  ad79x8_InUse

#define ad7918_Initialize             ad79x8_Initialize
//-- values for the "range" augment
     #define AD7918MODE_RANGE_VREF    (AD79x8MODE_RANGE_VREF)
     #define AD7918MODE_RANGE_2VREF   (AD79x8MODE_RANGE_2VREF)
//-- values for the "coding" augment
     #define AD7918MODE_CODING_1023   (AD79x8MODE_CODING_UNSIGNED)
     #define AD7918MODE_CODING_511    (AD79x8MODE_CODING_SIGNED)

#define ad7918_Close                  ad79x8_Close

#define ad7918_ChangeChannel          ad79x8_ChangeChannel

RBAPI(int) ad7918_Read(void);
//-- if the above function return AD7918_READFAIL, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL            (ERR_NOERROR + 310)


//AD7918 Multi-Channels Batch Mode Functions:
//--------------------------------------------
#define ad7918_InitializeMCH          ad79x8_InitializeMCH
//-- values for the "usedchannels" argument of the above functions
     #define AD7918_USECHANNEL0	      (AD79x8_USECHANNEL0)
     #define AD7918_USECHANNEL1		  (AD79x8_USECHANNEL1)
     #define AD7918_USECHANNEL2	      (AD79x8_USECHANNEL2)
     #define AD7918_USECHANNEL3		  (AD79x8_USECHANNEL3)
     #define AD7918_USECHANNEL4	      (AD79x8_USECHANNEL4)
     #define AD7918_USECHANNEL5       (AD79x8_USECHANNEL5)
     #define AD7918_USECHANNEL6       (AD79x8_USECHANNEL6)
     #define AD7918_USECHANNEL7       (AD79x8_USECHANNEL7)

#define ad7918_CloseMCH               ad79x8_Close

#define ad7918_ChangeChannels         ad79x8_ChangeChannels

RBAPI(int*) ad7918_ReadMCH(void);
/*---------------------------  end of AD7918  ----------------------------*/



/*******************************  AD7928  *********************************/

//AD7928 Channel-by-Channel Reading Function:
//--------------------------------------------
RBAPI(int) ad7928_ReadChannel(int channel, int range, int coding);  //don't use in continuous mode
//-- if the above function return AD7928_READFAIL, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL           (ERR_NOERROR + 310)
//   #define ERROR_ADC_NOSPI		 (ERR_NOERROR + 331)


//AD7928 Single-Channel Batch Mode Functions:
//--------------------------------------------
#define ad7928_InUse                  ad79x8_InUse

#define ad7928_Initialize             ad79x8_Initialize
//-- values for the "range" augment
     #define AD7928MODE_RANGE_VREF    (AD79x8MODE_RANGE_VREF)
     #define AD7928MODE_RANGE_2VREF   (AD79x8MODE_RANGE_2VREF)
//-- values for the "coding" augment
     #define AD7928MODE_CODING_4095   (AD79x8MODE_CODING_UNSIGNED)
     #define AD7928MODE_CODING_2047   (AD79x8MODE_CODING_SIGNED)

#define ad7928_Close                  ad79x8_Close

#define ad7928_ChangeChannel          ad79x8_ChangeChannel

RBAPI(int) ad7928_Read(void);
//-- if the above function return AD7928_READFAIL, ERR_Type may be settled as the following number:
//   #define ERROR_ADCFAIL            (ERR_NOERROR + 310)


//AD7928 Multi-Channels Batch Mode Functions:
//--------------------------------------------
#define ad7928_InitializeMCH          ad79x8_InitializeMCH
//-- values for the "usedchannels" argument of the above functions
     #define AD7928_USECHANNEL0	      (AD79x8_USECHANNEL0)
     #define AD7928_USECHANNEL1		  (AD79x8_USECHANNEL1)
     #define AD7928_USECHANNEL2	      (AD79x8_USECHANNEL2)
     #define AD7928_USECHANNEL3		  (AD79x8_USECHANNEL3)
     #define AD7928_USECHANNEL4	      (AD79x8_USECHANNEL4)
     #define AD7928_USECHANNEL5       (AD79x8_USECHANNEL5)
     #define AD7928_USECHANNEL6       (AD79x8_USECHANNEL6)
     #define AD7928_USECHANNEL7       (AD79x8_USECHANNEL7)

#define ad7928_CloseMCH               ad79x8_Close

#define ad7928_ChangeChannels         ad79x8_ChangeChannels

RBAPI(int*) ad7928_ReadMCH(void);
/*---------------------------  end of AD7928  ----------------------------*/

#ifdef __cplusplus
}
#endif

#endif

