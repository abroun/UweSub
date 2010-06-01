//------------------------------------------------------------------------------
// File: RollingBufferTests.h
// Desc: Unit tests for the rolling buffer
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <cxxtest/TestSuite.h>
#include <string.h>
#include "Common.h"
#include "UweSubPlugin/DataStructures/RollingBuffer.h"

//------------------------------------------------------------------------------
class RollingBufferTests : public CxxTest::TestSuite 
{
    //--------------------------------------------------------------------------
    public: virtual void setUp()
    {
        mBuffer.Init( BUFFER_SIZE );
    }
    
    //--------------------------------------------------------------------------
    public: virtual void tearDown()
    {
        mBuffer.Deinit();
    }
    
    
    //--------------------------------------------------------------------------
    public: void testClear()
    {
        mBuffer.Clear();
        
        TS_ASSERT( 0 == mBuffer.GetNumBytesInBuffer() );
        TS_ASSERT( BUFFER_SIZE == mBuffer.GetFreeSpace() );
    }
    
    //--------------------------------------------------------------------------
    public: void testAddBytes()
    {
        const U8 TEST_DATA[] = { '2', '6', '5', '5', 'a', '5', 'x', 'b', 'a' };
        
        mBuffer.Clear();
        bool bAddSuceeded = mBuffer.TryToAddBytes( TEST_DATA, sizeof( TEST_DATA ) );
        
        TS_ASSERT( bAddSuceeded );
        TS_ASSERT( mBuffer.GetNumBytesInBuffer() == sizeof( TEST_DATA ) );
        TS_ASSERT( mBuffer.GetFreeSpace() == BUFFER_SIZE - sizeof( TEST_DATA ) );
        
        U8 peekedAtData[ sizeof( TEST_DATA ) ];
        mBuffer.PeekAtBytes( peekedAtData, sizeof( TEST_DATA ) );
        TS_ASSERT( memcmp( TEST_DATA, peekedAtData, sizeof( TEST_DATA ) ) == 0 );
        
        // Second add should fail due to lack of space
        bAddSuceeded = mBuffer.TryToAddBytes( TEST_DATA, sizeof( TEST_DATA ) );
        TS_ASSERT( false == bAddSuceeded );
    }
    
    //--------------------------------------------------------------------------
    private: static const U32 BUFFER_SIZE = 15;
    private: RollingBuffer mBuffer;
};