//------------------------------------------------------------------------------
// File: RoBoardControl.cpp
// Desc: The python interface for accessing RoBoardControl classes and routines
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
#include <Python.h>
#include "structmember.h"

#include <math.h>

#include <opencv/cxcore.h>
#include <opencv/cv.h>
#include <opencv/cvwimage.h>
#include <opencv/highgui.h>

#include "ColourTracker/ColourTracker.h"

#include "sba.h"

//------------------------------------------------------------------------------
// IplImage conversion. Nicked from OpenCV Python bindings
//------------------------------------------------------------------------------
struct iplimage_t {
  PyObject_HEAD
  IplImage *a;
  PyObject *data;
  size_t offset;
};

//------------------------------------------------------------------------------
static bool RBC_ConvertPyObjectToIplImage( PyObject *o, IplImage **dst )
{
    iplimage_t *ipl = (iplimage_t*)o;
    void *buffer;
    Py_ssize_t buffer_len;
    
    if (PyString_Check(ipl->data)) 
    {
        cvSetData(ipl->a, PyString_AsString(ipl->data) + ipl->offset, ipl->a->widthStep);

        *dst = ipl->a;
        return true;
    } 
    else if (ipl->data && PyObject_AsWriteBuffer(ipl->data, &buffer, &buffer_len) == 0) 
    {   
        cvSetData(ipl->a, (void*)((char*)buffer + ipl->offset), ipl->a->widthStep);

        *dst = ipl->a;
        return true;
    } 
    else 
    {
        fprintf( stderr, "IplImage argument has no data" );
        return false;
    }
}

//------------------------------------------------------------------------------
static PyObject* RBC_Sin( PyObject* pSelf, PyObject* pArgs )
{
    float x;

    if ( !PyArg_ParseTuple( pArgs, "f", &x ) )
    {
        return NULL;
    }

    float result = sinf( x );
    return Py_BuildValue( "f", result );
}

//------------------------------------------------------------------------------
static double* PyListToIntArray( PyObject* pPyList )
{
    double* pResult = NULL;
    
    int listSize = PyList_Size( pPyList );
    if ( listSize >= 0 )
    {
        pResult = new double[ listSize ];
        
        for ( int i = 0; i < listSize; i++ )
        {
            PyObject* pFloat = PyList_GetItem( pPyList, i );
            pResult[ i ] = PyFloat_AsDouble( pFloat );
        }
    }
    
    return pResult;
}

//------------------------------------------------------------------------------
static PyObject* RBC_BundleAdjustment( PyObject* pSelf, PyObject* pArgs )
{
    PyObject* pCameraPyList;
    PyObject* pPoseGuessPyList;
    PyObject* pLandmarkPointPyList;

    if ( !PyArg_ParseTuple( pArgs, "OOO", &pCameraPyList, &pPoseGuessPyList, &pLandmarkPointPyList ) )
    {
        return NULL;
    }
    
    double* pCameraArray = PyListToIntArray( pCameraPyList );
    double* pPoseGuessArray = PyListToIntArray( pPoseGuessPyList );
    double* pLandmarkPointArray = PyListToIntArray( pLandmarkPointPyList );
    
    float result = sinf( 1.57f );
    
    delete [] pCameraArray;
    delete [] pPoseGuessArray;
    delete [] pLandmarkPointArray;
    
    return Py_BuildValue( "f", result );
}

//------------------------------------------------------------------------------
static PyMethodDef RoBoardControlMethods[] = 
{
    { "sin", RBC_Sin, METH_VARARGS, "Calculates the sine of the input" },
    { "bundleAdjustment", RBC_BundleAdjustment, METH_VARARGS, "Interface to the sba library" },

    { NULL, NULL, 0, NULL }        // Sentinel
};

//------------------------------------------------------------------------------
// BlobData
//------------------------------------------------------------------------------
typedef struct {
    PyObject_HEAD
    int number;
    BlobData mData;
} RBC_BlobDataObject;

//------------------------------------------------------------------------------
PyObject* RBC_BlobData_GetVisible( RBC_BlobDataObject* pSelf )
{
    return PyBool_FromLong( pSelf->mData.mbVisible );
}

//------------------------------------------------------------------------------
PyObject* RBC_BlobData_GetCentreX( RBC_BlobDataObject* pSelf )
{
    return PyFloat_FromDouble( pSelf->mData.mCentreX );
}

//------------------------------------------------------------------------------
PyObject* RBC_BlobData_GetCentreY( RBC_BlobDataObject* pSelf )
{
    return PyFloat_FromDouble( pSelf->mData.mCentreY );
}

//------------------------------------------------------------------------------
PyObject* RBC_BlobData_GetRadius( RBC_BlobDataObject* pSelf )
{
    return PyFloat_FromDouble( pSelf->mData.mRadius );
}

//------------------------------------------------------------------------------
static PyGetSetDef RBC_BlobData_GetterAndSetters[] = 
{
    { (char*)"visible", (getter)RBC_BlobData_GetVisible, (setter)NULL, (char*)"Blob visible", NULL },
    { (char*)"centreX", (getter)RBC_BlobData_GetCentreX, (setter)NULL, (char*)"X value of blob centre", NULL },
    { (char*)"centreY", (getter)RBC_BlobData_GetCentreY, (setter)NULL, (char*)"Y value of blob centre", NULL },
    { (char*)"radius", (getter)RBC_BlobData_GetRadius, (setter)NULL, (char*)"radius of blob", NULL },
    { NULL }  // Sentinel
};

//------------------------------------------------------------------------------
static PyTypeObject RBC_BlobDataType = 
{
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "RoBoardControl.BlobData", /*tp_name*/
    sizeof( RBC_BlobDataObject ), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    0,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "Information about a blob", /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    0,                      /* tp_methods */
    0,                      /* tp_members */
    RBC_BlobData_GetterAndSetters,           /* tp_getset */

};

//------------------------------------------------------------------------------
// ColourTracker
//------------------------------------------------------------------------------
typedef struct {
    PyObject_HEAD
    ColourTracker mTracker;
} RBC_ColourTrackerObject;

//------------------------------------------------------------------------------
static int RBC_ColourTracker_init( RBC_ColourTrackerObject* pSelf, PyObject* pArgs, PyObject* pKwds )
{
    float trackedHue = ColourTracker::DEFAULT_TRACKED_HUE; 
    float maxAbsHueDiff = ColourTracker::DEFAULT_MAX_ABS_HUE_DIFF;
    int calculateRadius = ColourTracker::DEFAULT_CALCULATE_RADIUS;

    static char* keyWorldList[] = 
    { 
        (char*)"trackedHue", 
        (char*)"maxAbsHueDiff", 
        (char*)"calculateRadius", 
        NULL 
    };

    if ( !PyArg_ParseTupleAndKeywords( pArgs, pKwds, "|ffi", keyWorldList,
                                      &trackedHue, &maxAbsHueDiff, &calculateRadius ) )
    {
        return -1;
    }

    pSelf->mTracker = ColourTracker( trackedHue, maxAbsHueDiff, ( 0 != calculateRadius ) );

    return 0;
}

//------------------------------------------------------------------------------
static PyObject* RBC_ColourTracker_Reset( RBC_ColourTrackerObject* pSelf )
{
    pSelf->mTracker.Reset();
    return Py_BuildValue( "" );
}

//------------------------------------------------------------------------------
static PyObject* RBC_ColourTracker_ProcessFrame( RBC_ColourTrackerObject* pSelf, PyObject* pArgs )
{
    PyObject* pFrame = NULL;

    if ( !PyArg_ParseTuple( pArgs, "O", &pFrame ) )
    {
        return NULL;
    }

    IplImage *pIplFrame = NULL;
    if ( !RBC_ConvertPyObjectToIplImage( pFrame, &pIplFrame ) )
    {
        return NULL;
    }
    IplImage* pProcessedFrame = pSelf->mTracker.ProcessFrame( pIplFrame );
    
    PyObject* pResult = PyString_FromStringAndSize(pProcessedFrame->imageData, pProcessedFrame->imageSize);
    cvReleaseImage( &pProcessedFrame );
    
    return pResult;
}

//------------------------------------------------------------------------------
static PyObject* RBC_ColourTracker_GetBlobData( RBC_ColourTrackerObject* pSelf )
{
    RBC_BlobDataObject* pBlobData = PyObject_NEW( RBC_BlobDataObject, &RBC_BlobDataType );
    pBlobData->mData = pSelf->mTracker.GetBlobData();
    
    return (PyObject*)pBlobData;
}

//------------------------------------------------------------------------------
static PyObject* RBC_ColourTracker_SetTrackedHue( RBC_ColourTrackerObject* pSelf, PyObject* pArgs, PyObject* pKwds )
{
    float trackedHue;
    float maxAbsHueDiff = ColourTracker::DEFAULT_MAX_ABS_HUE_DIFF;
    
    static char* keyWorldList[] = 
    { 
        (char*)"trackedHue", 
        (char*)"maxAbsHueDiff",
        NULL 
    };
        
    if ( !PyArg_ParseTupleAndKeywords( pArgs, pKwds, "f|f", keyWorldList,
        &trackedHue, &maxAbsHueDiff ) )
    {
        return NULL;
    }
    
    pSelf->mTracker.SetTrackedHue( trackedHue, maxAbsHueDiff );
    
    return Py_BuildValue( "" );
}

//------------------------------------------------------------------------------
static PyObject* RBC_ColourTracker_SetTrackedSaturation( RBC_ColourTrackerObject* pSelf, PyObject* pArgs, PyObject* pKwds )
{
    float trackedSaturation;
    float maxAbsSaturationDiff = ColourTracker::DEFAULT_MAX_ABS_SATURATION_DIFF;
    
    static char* keyWorldList[] = 
    { 
        (char*)"trackedSaturation", 
        (char*)"maxAbsSaturationDiff",
        NULL 
    };
    
    if ( !PyArg_ParseTupleAndKeywords( pArgs, pKwds, "f|f", keyWorldList,
        &trackedSaturation, &maxAbsSaturationDiff ) )
    {
        return NULL;
    }
    
    pSelf->mTracker.SetTrackedSaturation( trackedSaturation, maxAbsSaturationDiff );
    
    return Py_BuildValue( "" );
}

//------------------------------------------------------------------------------
static PyObject* RBC_ColourTracker_SetTrackedValue( RBC_ColourTrackerObject* pSelf, PyObject* pArgs, PyObject* pKwds )
{
    float trackedValue;
    float maxAbsValueDiff = ColourTracker::DEFAULT_MAX_ABS_VALUE_DIFF;
    
    static char* keyWorldList[] = 
    { 
        (char*)"trackedValue", 
        (char*)"maxAbsValueDiff", 
        NULL 
    };
    
    if ( !PyArg_ParseTupleAndKeywords( pArgs, pKwds, "f|f", keyWorldList,
        &trackedValue, &maxAbsValueDiff ) )
    {
        return NULL;
    }
    
    pSelf->mTracker.SetTrackedValue( trackedValue, maxAbsValueDiff );
    
    return Py_BuildValue( "" );
}

//------------------------------------------------------------------------------
static PyMethodDef RBC_ColourTrackerMethods[] = 
{
    { "reset", (PyCFunction)RBC_ColourTracker_Reset, METH_NOARGS, "Resets the tracker" },
    { "processFrame", (PyCFunction)RBC_ColourTracker_ProcessFrame, METH_VARARGS, "Processes the given frame" },
    { "getBlobData", (PyCFunction)RBC_ColourTracker_GetBlobData, METH_NOARGS, "Gets information about the tracked blob" },
    { "setTrackedHue", (PyCFunction)RBC_ColourTracker_SetTrackedHue, METH_VARARGS | METH_KEYWORDS, "Sets the hue being tracked" },
    { "setTrackedSaturation", (PyCFunction)RBC_ColourTracker_SetTrackedSaturation, METH_VARARGS | METH_KEYWORDS, "Sets the saturation being tracked" },
    { "setTrackedValue", (PyCFunction)RBC_ColourTracker_SetTrackedValue, METH_VARARGS | METH_KEYWORDS, "Sets the value being tracked" },
    

    { NULL, NULL, 0, NULL }        // Sentinel
};

//------------------------------------------------------------------------------
static PyTypeObject RBC_ColourTrackerType = 
{
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "RoBoardControl.ColourTracker", /*tp_name*/
    sizeof( RBC_ColourTrackerObject ), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    0,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "Tracks a coloured blob by looking for the centre of mass of appropriately coloured pixels", /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    RBC_ColourTrackerMethods,  /* tp_methods */
    0,                         /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)RBC_ColourTracker_init,      /* tp_init */
    0,                         /* tp_alloc */
0,                             /* tp_new */

};

//------------------------------------------------------------------------------
PyMODINIT_FUNC
initRoBoardControl()
{
    RBC_BlobDataType.tp_new = PyType_GenericNew;
    if ( PyType_Ready( &RBC_BlobDataType ) < 0 )
    {
        return;
    }

    RBC_ColourTrackerType.tp_new = PyType_GenericNew;
    if ( PyType_Ready( &RBC_ColourTrackerType ) < 0 )
    {
        return;
    }

    PyObject* pModule = Py_InitModule( "RoBoardControl", RoBoardControlMethods );

    Py_INCREF( &RBC_BlobDataType );
    PyModule_AddObject( pModule, "BlobData", (PyObject *)&RBC_BlobDataType );
    Py_INCREF( &RBC_ColourTrackerType );
    PyModule_AddObject( pModule, "ColourTracker", (PyObject *)&RBC_ColourTrackerType );

}





