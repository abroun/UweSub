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
    digitalWrite( SS_PIN, HIGH );

    SPCR = 0;
    SPCR = (0<<SPIE)    // Interrupt disabled 
        | (1<<SPE)      // SPI enabled
        | (1<<MSTR)     // Master mode
        | (0<<CPOL)     // Clock is low when idle
        | (1<<SPR1)
        | (1<<SPR0);
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
    //digitalWrite( SS_PIN, LOW );
    SPI_WriteRead( firstCommandByte );       
    SPI_WriteRead( secondCommandByte );
    //digitalWrite( SS_PIN, HIGH );
   
    // PAuse if needed to give the sensor time to process the command
    if ( delayMS > 0 )
    {
        delay( delayMS );
    }
                
    // Read the data
    SPI_SetSampleMode( eSM_Trailing );
    //digitalWrite( SS_PIN, LOW );
    U16 result = ( SPI_WriteRead( 0x00 ) << 8 );       
    result |= SPI_WriteRead( 0x00 );
    //digitalWrite( SS_PIN, HIGH );

    return result;
}

//------------------------------------------------------------------------------
U16 CalculateCRC( U8* pData, U32 numBytes )
{
    U32 index = 0;
    U16 crc = 0;

    while( index < numBytes )
    {
        crc = (U8)(crc >> 8) | (crc << 8);
        crc ^= pData[ index++ ];
        crc ^= (U8)(crc & 0xff) >> 4;
        crc ^= (crc << 8) << 4;
        crc ^= ((crc & 0xff) << 4) << 1;
    }
    
    return crc;
}

//------------------------------------------------------------------------------
// Streams the data back to the controlling computer over serial
void SendData( S32 pressure, S32 temperature )
{
    // Construct a simple message with header, byte count and then CRC at the end
    const U8 HEADER_0 = 0xAB;
    const U8 HEADER_1 = 0xDE;
    
    U8 buffer[ 14 ];
    buffer[ 0 ] = HEADER_0;
    buffer[ 1 ] = HEADER_1;
    (*(U16*)&buffer[ 2 ]) = sizeof( buffer ); // byte count
    (*(S32*)&buffer[ 4 ]) = pressure;
    (*(S32*)&buffer[ 8 ]) = temperature;
    (*(S32*)&buffer[ 12 ]) = CalculateCRC( buffer, sizeof( buffer ) - 2 );
    
    Serial.write( buffer, sizeof( buffer ) );
}

//------------------------------------------------------------------------------
void setup()
{
    Serial.begin( 57600 );
    SPI_Setup();  
    
    delay( 100 );    // Give the sensor time to start up
    gState = eS_GettingCalibrationConstants;
    
    // Reset the sensor
    SPI_SetSampleMode( eSM_Leading );
    //digitalWrite( SS_PIN, LOW );
    SPI_WriteRead( 0x15 );
    SPI_WriteRead( 0x55 );
    SPI_WriteRead( 0x40 );
    //digitalWrite( SS_PIN, HIGH );
    
    delay( 100 ); 
}

//------------------------------------------------------------------------------
void loop()
{
    //delay( 1000 );
    //SPI_SetSampleMode( eSM_Trailing );
    /*digitalWrite( SS_PIN, LOW );
    byte num = SPI_WriteRead( 0x00 );
    digitalWrite( SS_PIN, HIGH );
    Serial.println( (int)num );
    return;*/
    
    switch ( gState )
    {
        case eS_GettingCalibrationConstants:
        {
            U16 calibrationWords[ 4 ];
            
            // Read the calibration words
            calibrationWords[ 0 ] = ReadDataFromSensor( 0x1D, 0x50, 10 );
            calibrationWords[ 1 ] = ReadDataFromSensor( 0x1D, 0x60, 10 );
            calibrationWords[ 2 ] = ReadDataFromSensor( 0x1D, 0x90, 10 );
            calibrationWords[ 3 ] = ReadDataFromSensor( 0x1D, 0xA0, 10 );
            
            // Extract coefficients
            C1 = calibrationWords[ 0 ] >> 1;
            C2 = ( ( calibrationWords[ 2 ] & 0x3F ) << 6 ) | ( calibrationWords[ 3 ] & 0x3F ); 
            C3 = ( calibrationWords[ 2 ] & 0xFFC0 ) >> 6;
            C4 = ( calibrationWords[ 3 ] & 0xFFC0 ) >> 6;
            C5 = ( ( calibrationWords[ 0 ] & 0x1 ) << 10 ) | ( ( calibrationWords[ 1 ] & 0xFFC0 ) >> 6 );
            C6 = calibrationWords[ 1 ] & 0x3F;
            
            gState = eS_StreamingData;
            
            Serial.println( C1 );
            Serial.println( C2 );            
            Serial.println( C3 );
            Serial.println( C4 );
            Serial.println( C5 );
            Serial.println( C6 );
            Serial.println( "Hi" );
            
            break;
        }
        case eS_StreamingData:
        {
            // Read out the pressure
            U16 pressureData = ReadDataFromSensor( 0x0F, 0x40, 35 );
            
            // Read out the temperature
            U16 tempData = ReadDataFromSensor( 0x0F, 0x20, 35 );
         
            // TODO: Remove this when we attach sensor
            C1 = C2 = C3 = C4 = C5 = C6 = 0;
            pressureData = tempData = 0;
            
            // Calculate the calibrated temperature and pressure values
            // Calculations taken from MS5540C datasheet
            // Use S32s to ensure that we have enough precision
            S32 UT1 = 8*C5 + 20224;
            S32 dT = tempData - UT1;
            S32 TEMP = 200 + (dT*(C6 + 50))>>10;
            
            // Temperature compensated pressure
            S32 OFF = C2*4 + (((C4-512)*dT))>>12;
            S32 SENS = C1 + (C3*dT)>>10 + 24576;
            S32 X = (SENS*(pressureData-7168))>>14 - OFF;
            S32 P = (X*10)>>5 + 250*10;
            
            // Now perform second order temperature compensation
            S32 T2;
            S32 P2;
            
            if ( TEMP < 200 )
            {
                // Low temperatures
                T2 = (11*(C6+24)*(200-TEMP)*(200-TEMP))>>20;
                P2 = (3*T2*(P-3500))>>14;
            }
            else if ( TEMP >= 200 && TEMP <= 450 )
            {
                // No correction
                T2 = 0;
                P2 = 0;
            }
            else // TEMP > 450
            {
                T2 = (3*(C6+24)*(450-TEMP)*(450-TEMP))>>20;
                P2 = (T2*(P-10000))>>13;
            }
            
            TEMP = TEMP - T2;
            P = P - P2;
            
            // Send over serial
//            SendData( P, TEMP );
            break;
        }
    }
}



