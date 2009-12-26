//------------------------------------------------------------------------------
// A control program that tries to follow an orange buoy
//------------------------------------------------------------------------------
#include <stdio.h>

#include <cv.h>
#include <cvaux.h>
#include <highgui.h>

//------------------------------------------------------------------------------
int main()
{   
    CvCapture* pCapture = cvCreateFileCapture( "/home/abroun/Downloads/SAUC-E Videos/buoy.avi" );
    if ( NULL == pCapture )
    {
        fprintf( stderr, "Error: Unable to connect to video source\n" );
        return -1;
    }

   
    /*cvNamedWindow( "win1", CV_WINDOW_AUTOSIZE ); 
    cvMoveWindow( "win1", 100, 100 ); // offset from the UL corner of the screen

    cvShowImage( "win1", pImg );*/
    

    bool bAllFramesProcessed = false;
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

    cvReleaseCapture( &pCapture );

    return 0;
}
