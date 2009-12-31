# Module for determining Python bindings configuration options

# Options to enable Python bindings
OPTION( ENABLE_PYTHON "Enable Python bindings" ON )

IF ( ENABLE_PYTHON )
    # Check for Python interpreter (which also defines PYTHON_EXECUTABLE)
    FIND_PACKAGE( PythonInterp )
    IF ( NOT PYTHONINTERP_FOUND )
        MESSAGE(STATUS "WARNING: "
        "python interpreter not found. Disabling python bindings" )
        SET( ENABLE_PYTHON OFF CACHE BOOL "Enable Python bindings" FORCE )
    ENDIF( NOT PYTHONINTERP_FOUND )
ENDIF( ENABLE_PYTHON )

IF ( ENABLE_PYTHON )
    # Check for Python libraries which defines
    #  PYTHON_LIBRARIES     = path to the python library
    #  PYTHON_INCLUDE_PATH  = path to where Python.h is found
    FIND_PACKAGE( PythonLibs )
    IF ( NOT PYTHON_LIBRARIES OR NOT PYTHON_INCLUDE_PATH )
        MESSAGE( STATUS "WARNING: "
          "python library and/or header not found. Disabling python bindings")
        SET( ENABLE_PYTHON OFF CACHE BOOL "Enable Python bindings" FORCE )
    ENDIF ( NOT PYTHON_LIBRARIES OR NOT PYTHON_INCLUDE_PATH )
ENDIF( ENABLE_PYTHON )

IF ( ENABLE_PYTHON )
    # Get the installation directory from distutils
    EXECUTE_PROCESS(
        COMMAND
        ${PYTHON_EXECUTABLE} -c "from distutils import sysconfig; print sysconfig.get_python_lib(1,0,prefix='${CMAKE_INSTALL_PREFIX}')"
        OUTPUT_VARIABLE PYTHON_INSTDIR
        OUTPUT_STRIP_TRAILING_WHITESPACE )
ENDIF( ENABLE_PYTHON )
