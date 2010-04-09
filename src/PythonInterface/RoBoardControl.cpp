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
#include "imgproj.h"

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

/* pointers to additional data, used for computed image projections and their jacobians */
struct globs_{
    double *rot0params; /* initial rotation parameters, combined with a local rotation parameterization */
    double *intrcalib; /* the 5 intrinsic calibration parameters in the order [fu, u0, v0, ar, skew],
                      * where ar is the aspect ratio fv/fu.
                      * Used only when calibration is fixed for all cameras;
                      * otherwise, it is null and the intrinsic parameters are
                      * included in the set of motion parameters for each camera
                      */
  int nccalib; /* number of calibration parameters that must be kept constant.
                * 0: all parameters are free 
                * 1: skew is fixed to its initial value, all other parameters vary (i.e. fu, u0, v0, ar) 
                * 2: skew and aspect ratio are fixed to their initial values, all other parameters vary (i.e. fu, u0, v0)
                * 3: meaningless
                * 4: skew, aspect ratio and principal point are fixed to their initial values, only the focal length varies (i.e. fu)
                * 5: all intrinsics are kept fixed to their initial values
                * >5: meaningless
                * Used only when calibration varies among cameras
                */

  int ncdist; /* number of distortion parameters in Bouguet's model that must be kept constant.
               * 0: all parameters are free 
               * 1: 6th order radial distortion term (kc[4]) is fixed
               * 2: 6th order radial distortion and one of the tangential distortion terms (kc[3]) are fixed
               * 3: 6th order radial distortion and both tangential distortion terms (kc[3], kc[2]) are fixed [i.e., only 2nd & 4th order radial dist.]
               * 4: 4th & 6th order radial distortion terms and both tangential distortion ones are fixed [i.e., only 2nd order radial dist.]
               * 5: all distortion parameters are kept fixed to their initial values
               * >5: meaningless
               * Used only when calibration varies among cameras and distortion is to be estimated
               */
  int cnp, pnp, mnp; /* dimensions */

    double *ptparams; /* needed only when bundle adjusting for camera parameters only */
    double *camparams; /* needed only when bundle adjusting for structure parameters only */
} globs;

/* unit quaternion from vector part */
#define _MK_QUAT_FRM_VEC(q, v){                                     \
  (q)[1]=(v)[0]; (q)[2]=(v)[1]; (q)[3]=(v)[2];                      \
  (q)[0]=sqrt(1.0 - (q)[1]*(q)[1] - (q)[2]*(q)[2]- (q)[3]*(q)[3]);  \
}

#define FULLQUATSZ 4

/*
 * fast multiplication of the two quaternions in q1 and q2 into p
 * this is the second of the two schemes derived in pg. 8 of
 * T. D. Howell, J.-C. Lafon, The complexity of the quaternion product, TR 75-245, Cornell Univ., June 1975.
 *
 * total additions increase from 12 to 27 (28), but total multiplications decrease from 16 to 9 (12)
 */
inline static void quatMultFast(double q1[FULLQUATSZ], double q2[FULLQUATSZ], double p[FULLQUATSZ])
{
double t1, t2, t3, t4, t5, t6, t7, t8, t9;
//double t10, t11, t12;

  t1=(q1[0]+q1[1])*(q2[0]+q2[1]);
  t2=(q1[3]-q1[2])*(q2[2]-q2[3]);
  t3=(q1[1]-q1[0])*(q2[2]+q2[3]);
  t4=(q1[2]+q1[3])*(q2[1]-q2[0]);
  t5=(q1[1]+q1[3])*(q2[1]+q2[2]);
  t6=(q1[1]-q1[3])*(q2[1]-q2[2]);
  t7=(q1[0]+q1[2])*(q2[0]-q2[3]);
  t8=(q1[0]-q1[2])*(q2[0]+q2[3]);

#if 0
  t9 =t5+t6;
  t10=t7+t8;
  t11=t5-t6;
  t12=t7-t8;

  p[0]= t2 + 0.5*(-t9+t10);
  p[1]= t1 - 0.5*(t9+t10);
  p[2]=-t3 + 0.5*(t11+t12);
  p[3]=-t4 + 0.5*(t11-t12);
#endif

  /* following fragment it equivalent to the one above */
  t9=0.5*(t5-t6+t7+t8);
  p[0]= t2 + t9-t5;
  p[1]= t1 - t9-t6;
  p[2]=-t3 + t9-t8;
  p[3]=-t4 + t9-t7;
}

/*** MEASUREMENT VECTOR AND JACOBIAN COMPUTATION FOR THE EXPERT DRIVERS ***/

/* FULL BUNDLE ADJUSTMENT, I.E. SIMULTANEOUS ESTIMATION OF CAMERA AND STRUCTURE PARAMETERS */

/* Given a parameter vector p made up of the 3D coordinates of n points and the parameters of m cameras, compute in
 * hx the prediction of the measurements, i.e. the projections of 3D points in the m images. The measurements
 * are returned in the order (hx_11^T, .. hx_1m^T, ..., hx_n1^T, .. hx_nm^T)^T, where hx_ij is the predicted
 * projection of the i-th point on the j-th camera.
 * Notice that depending on idxij, some of the hx_ij might be missing
 *
 */
static void img_projsRTS_x(double *p, struct sba_crsm *idxij, int *rcidxs, int *rcsubs, double *hx, void *adata)
{
  register int i, j;
  int cnp, pnp, mnp;
  double *pa, *pb, *pqr, *pt, *ppt, *pmeas, *Kparms, *pr0, lrot[FULLQUATSZ], trot[FULLQUATSZ];
  //int n;
  int m, nnz;
  struct globs_ *gl;

  gl=(struct globs_ *)adata;
  cnp=gl->cnp; pnp=gl->pnp; mnp=gl->mnp;
  Kparms=gl->intrcalib;

  //n=idxij->nr;
  m=idxij->nc;
  pa=p; pb=p+m*cnp;

  for(j=0; j<m; ++j){
    /* j-th camera parameters */
    pqr=pa+j*cnp;
    pt=pqr+3; // quaternion vector part has 3 elements
    pr0=gl->rot0params+j*FULLQUATSZ; // full quat for initial rotation estimate
    _MK_QUAT_FRM_VEC(lrot, pqr);
    quatMultFast(lrot, pr0, trot); // trot=lrot*pr0

    nnz=sba_crsm_col_elmidxs(idxij, j, rcidxs, rcsubs); /* find nonzero hx_ij, i=0...n-1 */

    for(i=0; i<nnz; ++i){
      ppt=pb + rcsubs[i]*pnp;
      pmeas=hx + idxij->val[rcidxs[i]]*mnp; // set pmeas to point to hx_ij

      calcImgProjFullR(Kparms, trot, pt, ppt, pmeas); // evaluate Q in pmeas
      //calcImgProj(Kparms, pr0, pqr, pt, ppt, pmeas); // evaluate Q in pmeas
    }
  }
}

/* Given a parameter vector p made up of the 3D coordinates of n points and the parameters of m cameras, compute in
 * jac the jacobian of the predicted measurements, i.e. the jacobian of the projections of 3D points in the m images.
 * The jacobian is returned in the order (A_11, ..., A_1m, ..., A_n1, ..., A_nm, B_11, ..., B_1m, ..., B_n1, ..., B_nm),
 * where A_ij=dx_ij/db_j and B_ij=dx_ij/db_i (see HZ).
 * Notice that depending on idxij, some of the A_ij, B_ij might be missing
 *
 */
static void img_projsRTS_jac_x(double *p, struct sba_crsm *idxij, int *rcidxs, int *rcsubs, double *jac, void *adata)
{
  register int i, j;
  int cnp, pnp, mnp;
  double *pa, *pb, *pqr, *pt, *ppt, *pA, *pB, *Kparms, *pr0;
  //int n;
  int m, nnz, Asz, Bsz, ABsz;
  struct globs_ *gl;
  
  gl=(struct globs_ *)adata;
  cnp=gl->cnp; pnp=gl->pnp; mnp=gl->mnp;
  Kparms=gl->intrcalib;

  //n=idxij->nr;
  m=idxij->nc;
  pa=p; pb=p+m*cnp;
  Asz=mnp*cnp; Bsz=mnp*pnp; ABsz=Asz+Bsz;

  for(j=0; j<m; ++j){
    /* j-th camera parameters */
    pqr=pa+j*cnp;
    pt=pqr+3; // quaternion vector part has 3 elements
    pr0=gl->rot0params+j*FULLQUATSZ; // full quat for initial rotation estimate

    nnz=sba_crsm_col_elmidxs(idxij, j, rcidxs, rcsubs); /* find nonzero hx_ij, i=0...n-1 */

    for(i=0; i<nnz; ++i){
      ppt=pb + rcsubs[i]*pnp;
      pA=jac + idxij->val[rcidxs[i]]*ABsz; // set pA to point to A_ij
      pB=pA  + Asz; // set pB to point to B_ij

      calcImgProjJacRTS(Kparms, pr0, pqr, pt, ppt, (double (*)[6])pA, (double (*)[3])pB); // evaluate dQ/da, dQ/db in pA, pB
    }
  }
}

//------------------------------------------------------------------------------
static double* PyListToDoubleArray( PyObject* pPyList )
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
static char* PyListToVisibilityMask( PyObject* pPyList )
{
    char* pResult = NULL;
    
    int listSize = PyList_Size( pPyList );
    if ( listSize >= 0 )
    {
        pResult = new char[ listSize ];
        
        for ( int i = 0; i < listSize; i++ )
        {
            PyObject* pInt = PyList_GetItem( pPyList, i );
            pResult[ i ] = ( PyInt_AsLong( pInt ) == 0 ? 0 : 1 );
        }
    }
    
    return pResult;
}

static const int NUM_FRAME_COORDS = 6;
static const int NUM_LANDMARK_COORDS = 3;
static const int NUM_2D_PROJECTION_COORDS = 2;
static const int CAMERA_ARRAY_LENGTH = 5;
static const int QUATERNION_SIZE = 4;

//------------------------------------------------------------------------------
static PyObject* RBC_BundleAdjustment( PyObject* pSelf, PyObject* pArgs )
{
    int numFrames;
    int numLandmarks;
    int num2DProjections;
    PyObject* pMotionStructPyList;
    PyObject* pInitialRotationPyList;
    PyObject* pLandmarkProjectionPointPyList;
    PyObject* pLandmarkVisibilityPyList;
    PyObject* pCameraPyList;

    if ( !PyArg_ParseTuple( pArgs, "iiiOOOOO", 
        &numFrames, &numLandmarks, &num2DProjections,
        &pMotionStructPyList, &pInitialRotationPyList, 
        &pLandmarkProjectionPointPyList, &pLandmarkVisibilityPyList, 
        &pCameraPyList ) )
    {
        return NULL;
    }
    
    // Check that the parameters are consistent
    if ( PyList_Size( pMotionStructPyList )  !=
        numFrames * NUM_FRAME_COORDS + numLandmarks * NUM_LANDMARK_COORDS )
    {
        fprintf( stderr, "Error: Incorrect size for motion list\n" );
        return NULL;
    }
    
    if ( PyList_Size( pInitialRotationPyList )  != numFrames * QUATERNION_SIZE )
    {
        fprintf( stderr, "Error: Incorrect size for inital rotation list\n" );
        return NULL;
    }
    
    if ( PyList_Size( pLandmarkProjectionPointPyList )  != 
        num2DProjections * NUM_2D_PROJECTION_COORDS )
    {
        fprintf( stderr, "Error: Incorrect size for 2D projection list\n" );
        return NULL;
    }
    
    if ( PyList_Size( pLandmarkVisibilityPyList )  != numFrames * numLandmarks )
    {
        fprintf( stderr, "Error: Incorrect size for visibility list\n" );
        return NULL;
    }
    
    if ( PyList_Size( pCameraPyList )  != CAMERA_ARRAY_LENGTH )
    {
        fprintf( stderr, "Error: Incorrect size for camera list\n" );
        return NULL;
    }
    
    double* pMotionStruct = PyListToDoubleArray( pMotionStructPyList );
    double* pInitialRotations = PyListToDoubleArray( pInitialRotationPyList );
    double* pLandmarkProjectionPoints = PyListToDoubleArray( pLandmarkProjectionPointPyList );
    char* pLandmarkVisibilityMask = PyListToVisibilityMask( pLandmarkVisibilityPyList );
    double* pCameraArray = PyListToDoubleArray( pCameraPyList );
    
    /* set up globs structure */
    globs.cnp = NUM_FRAME_COORDS; 
    globs.pnp = NUM_LANDMARK_COORDS; 
    globs.mnp = NUM_2D_PROJECTION_COORDS;
    globs.rot0params = pInitialRotations;
    globs.intrcalib = pCameraArray;
    globs.ptparams=NULL;
    globs.camparams=NULL;
    
    double opts[SBA_OPTSSZ];
    double info[SBA_INFOSZ];
    
    opts[0]=SBA_INIT_MU; opts[1]=SBA_STOP_THRESH; opts[2]=SBA_STOP_THRESH;
    opts[3]=SBA_STOP_THRESH;
    //opts[3]=0.05*numprojs; // uncomment to force termination if the average reprojection error drops below 0.05
    opts[4]=0.0;
    //opts[4]=1E-05; // uncomment to force termination if the relative reduction in the RMS reprojection error drops below 1E-05

    
    const int MAXITER2 = 150;
    const int VERBOSE = 1;
    int numConstFrames = 0;
    int sbaResult = sba_motstr_levmar_x( 
        numLandmarks, 0, numFrames, numConstFrames, 
        pLandmarkVisibilityMask, pMotionStruct, 
        NUM_FRAME_COORDS, NUM_LANDMARK_COORDS,
        pLandmarkProjectionPoints, NULL, NUM_2D_PROJECTION_COORDS,
        img_projsRTS_x,         // Error function
        img_projsRTS_jac_x,     // Jacobian of error function (set to null) for non analytic jacobian
        (void *)(&globs), MAXITER2, VERBOSE, opts, info);
    
    delete [] pMotionStruct;
    delete [] pInitialRotations;
    delete [] pLandmarkProjectionPoints;
    delete [] pLandmarkVisibilityMask;
    delete [] pCameraArray;
    
    return Py_BuildValue( "i", sbaResult );
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





