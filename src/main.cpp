//------------------------------------------------------------------------------
// A control program that tries to follow an orange buoy
//------------------------------------------------------------------------------
#include <stdio.h>
#include <libplayerc/playerc.h>
#include <time.h>

//------------------------------------------------------------------------------
timespec GetTimeDiff( const timespec& end, const timespec& start )
{
  timespec result;
  
  if ( end.tv_nsec < start.tv_nsec ) 
  {
      result.tv_sec = end.tv_sec - start.tv_sec - 1;
      result.tv_nsec = 1000000000 + end.tv_nsec - start.tv_nsec;
  } 
  else 
  {
      result.tv_sec = end.tv_sec - start.tv_sec;
      result.tv_nsec = end.tv_nsec - start.tv_nsec;
  }
  return result;
}
    
//------------------------------------------------------------------------------
double ConvertToSeconds( const timespec& t )
{
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

//------------------------------------------------------------------------------
int main()
{   
    /*CvCapture* pCapture = cvCreateFileCapture( "/home/abroun/Downloads/SAUC-E Videos/buoy.avi" );
    if ( NULL == pCapture )
    {
        fprintf( stderr, "Error: Unable to connect to video source\n" );
        return -1;
    }*/

   
    /*cvNamedWindow( "win1", CV_WINDOW_AUTOSIZE ); 
    cvMoveWindow( "win1", 100, 100 ); // offset from the UL corner of the screen

    cvShowImage( "win1", pImg );*/
    

    /*bool bAllFramesProcessed = false;
    int frameIdx = 0;
    while ( !bAllFramesProcessed )
    {
        IplImage* pImg = NULL; 
        if( !cvGrabFrame( pCapture ) )
        {              
            // Frames finished 
            bAllFramesProcessed = true;
        }
        else
        {
            pImg = cvRetrieveFrame( pCapture );
            IplImage* pHSVImg = cvCloneImage( pImg );
            cvCvtColor( pImg, pHSVImg, CV_RGB2HSV );
            IplImage* pHImg = cvCreateImage( cvSize( pImg->width, pImg->height ), pImg->depth, 1 );

            cvSplit( pHSVImg, pHImg, NULL, NULL, NULL );

            char buffer[ 128 ];
            snprintf( buffer, sizeof( buffer ), "output/out_%i.png", frameIdx );
            buffer[ sizeof( buffer ) - 1 ] = '\0';
                
            cvSaveImage( buffer, pHImg );
            frameIdx++;
        }
    } 

    cvReleaseCapture( &pCapture );*/
    
    playerc_client_t* pPlayerClient = playerc_client_create( NULL, "localhost", 6665 );
    playerc_client_connect( pPlayerClient );
    
    playerc_camera_t* pPlayerCamera = playerc_camera_create( pPlayerClient, 0 );
    playerc_camera_subscribe( pPlayerCamera, PLAYER_OPEN_MODE );
    
    playerc_client_datamode( pPlayerClient, PLAYERC_DATAMODE_PULL );
    playerc_client_set_replace_rule( pPlayerClient, -1, -1, PLAYER_MSGTYPE_DATA, -1, 1 );
    
    timespec startTime;
    timespec endTime;
    
    while ( 1 )
    {
        
        
        if ( playerc_client_peek( pPlayerClient, 0 ) > 0 )
        {
            clock_gettime( CLOCK_REALTIME, &startTime );
            
            playerc_client_read( pPlayerClient );
            if ( PLAYER_CAMERA_COMPRESS_RAW != pPlayerCamera->compression )
            {
                playerc_camera_decompress( pPlayerCamera );
            }
            if ( PLAYER_CAMERA_COMPRESS_RAW != pPlayerCamera->compression )
            {
                fprintf( stderr, "Warning: Unable to decompress image\n" );
            }
            
            //playerc_camera_save( pPlayerCamera, "testoutput.ppm" );
            
            clock_gettime( CLOCK_REALTIME, &endTime );
            printf( "Call took %2.3fms\n", ConvertToSeconds( GetTimeDiff( endTime, startTime ) ) * 1000.0 );
        }
    }

    return 0;
}
