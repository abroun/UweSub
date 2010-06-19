#-------------------------------------------------------------------------------
INCLUDE( ${PROJECT_SOURCE_DIR}/cmake/utils.cmake )

#-------------------------------------------------------------------------------
# Include all the search paths for headers
INCLUDE_DIRECTORIES(
    .
    ${global_include_dirs} )

SET( srcFiles 
    HighPrecisionTime.cpp 
    Utils.cpp
    MathUtils.cpp )

ADD_LIBRARY( common ${srcFiles} )

