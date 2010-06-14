#include <avr/io.h>
#include "WProgram.h"
#include "DepthSensor.h"

// Conversion coefficients
U16 C1 = 0;
U16 C2 = 0;
U16 C3 = 0;
U16 C4 = 0;
U16 C5 = 0;
U16 C6 = 0;

//------------------------------------------------------------------------------
// Globals
volatile S16 gNumBytesSent = 0;
eState gState = eS_Invalid;

//------------------------------------------------------------------------------
void SPI_SetSampleMode( eSampleMode sampleMode )
{
    U8 curSPCR = SPCR;
    if ( eSM_Leading == sampleMode )
    {
        SPCR = curSPCR & ~(1<<CPHA);    // Clear CPHA
    }
    else // eSM_Trailing == sampleMode
    {
        SPCR = curSPCR | (1<<CPHA);     // Set CPHA
    }
}

//------------------------------------------------------------------------------
void SPI_Setup()
{
    // Setup the SPI as a master
    U8 tmp;

    // initialize the SPI pins
    pinMode( SCK_PIN, OUTPUT );
    pinMode( MOSI_PIN, OUTPUT );
    pinMode( MISO_PIN, INPUT );
    pinMode( SS_PIN, OUTPUT );

    SPCR = 0;
    SPCR = (0<<SPIE)    // Interrupt disabled 
        | (1<<SPE)      // SPI enabled
        | (1<<MSTR)     // Master mode
        | (0<<CPOL);    // Clock is low when idle
    tmp = SPSR;  // Clears any existing interrupt
    tmp = SPDR;
}

//------------------------------------------------------------------------------
U8 SPI_WriteRead( U8 dataout )
{
  // Put Slave Data On SPDR
  SPDR = dataout;

  // Wait for transmission complete
  while ( !(SPSR & (1<<SPIF)) );

  // Return Serial In Value (MISO)
  return SPDR;
}

//------------------------------------------------------------------------------
U16 ReadDataFromSensor( U8 firstCommandByte, U8 secondCommandByte, S16 delayMS = 0 )
{
    // Send command
    SPI_SetSampleMode( eSM_Leading );
    SPI_WriteRead( firstCommandByte );       
    SPI_WriteRead( secondCommandByte );
   
    // PAuse if needed to give the sensor time to process the command
    if ( delayMS > 0 )
    {
        delay( delayMS );
    }
                
    // Read the data
    SPI_SetSampleMode( eSM_Trailing );
    U16 result = ( SPI_WriteRead( 0x00 ) << 8 );       
    result |= SPI_WriteRead( 0x00 );

    return result;
}

//------------------------------------------------------------------------------
void setup()
{
    Serial.begin( 57600 );
    SPI_Setup();  
    
    delay( 100 );    // Give the sensor time to start up
    gState = eS_GettingCalibrationConstants;
}

//------------------------------------------------------------------------------
void loop()
{
    switch ( gState )
    {
        case eS_GettingCalibrationConstants:
        {
            U16 calibrationWords[ 4 ];
            
            // Read the calibration words
            calibrationWords[ 0 ] = ReadDataFromSensor( 0x1D, 0x50 );
            calibrationWords[ 1 ] = ReadDataFromSensor( 0x1D, 0x60 );
            calibrationWords[ 2 ] = ReadDataFromSensor( 0x1D, 0x90 );
            calibrationWords[ 3 ] = ReadDataFromSensor( 0x1D, 0xA0 );
            
            // Extract coefficients
            C1 = calibrationWords[ 0 ] >> 1;
            C2 = ( ( calibrationWords[ 2 ] & 0x3F ) << 6 ) | ( calibrationWords[ 3 ] & 0x3F ); 
            C3 = ( calibrationWords[ 2 ] & 0xFFC0 ) >> 6;
            C4 = ( calibrationWords[ 3 ] & 0xFFC0 ) >> 6;
            C5 = ( ( calibrationWords[ 0 ] & 0x1 ) << 10 ) | ( ( calibrationWords[ 1 ] & 0xFFC0 ) >> 6 );
            C6 = calibrationWords[ 1 ] & 0x3F;
            
            gState = eS_StreamingData;
            
            break;
        }
        case eS_StreamingData:
        {
            // Read out the temperature
            //U16 tempData = 
            
            // Read out the pressure
            
            // Calculate the calibrated temperature and pressure values
            
            // Send over serial
            break;
        }
    }
}



