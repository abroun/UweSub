typedef long S32;
typedef unsigned long U32;
typedef short S16;
typedef unsigned short U16;
typedef char S8;
typedef unsigned char U8;
typedef float F32;

#define SCK_PIN   13
#define MISO_PIN  12
#define MOSI_PIN  11
#define SS_PIN    10

//------------------------------------------------------------------------------
enum eState
{
    eS_Invalid = -1,
    eS_GettingCalibrationConstants,
    eS_StreamingData,
    eS_NumStates
};

//------------------------------------------------------------------------------
enum eSampleMode
{
    eSM_Leading,    // SPI samples on the leading (rising) clock edge
    eSM_Trailing,   // SPI samples on the trailing (falling) clock edge
};
