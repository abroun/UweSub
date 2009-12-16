#-------------------------------------------------------------------------------
# RoBoardControl CMake file
#-------------------------------------------------------------------------------
CMAKE_MINIMUM_REQUIRED( VERSION 2.4.6 FATAL_ERROR )
PROJECT( RoBoardControl )

INCLUDE( FindPkgConfig )
INCLUDE( ${PROJECT_SOURCE_DIR}/cmake/utils.cmake )

INIT_LISTS()
RESET_LISTS()

#-------------------------------------------------------------------------------
# Build type cflags
SET(CMAKE_C_FLAGS_RELEASE " -O3 -DNDEBUG -Wall " CACHE INTERNAL "C Flags for release" FORCE )
SET(CMAKE_C_FLAGS_DEBUG " -ggdb " CACHE INTERNAL "C Flags for debug" FORCE )

#-------------------------------------------------------------------------------
# Build type link flags
SET( CMAKE_LINK_FLAGS_RELEASE "" CACHE INTERNAL "Link flags for release" FORCE )
SET( CMAKE_LINK_FLAGS_DEBUG "" CACHE INTERNAL "Link flags for debug" FORCE )

#-------------------------------------------------------------------------------
# Set the default build type
IF( NOT CMAKE_BUILD_TYPE )
  SET ( CMAKE_BUILD_TYPE "release" CACHE STRING 
    "Choose the type of build, options are: debug release" FORCE )
ENDIF( NOT CMAKE_BUILD_TYPE )
STRING( TOUPPER ${CMAKE_BUILD_TYPE} CMAKE_BUILD_TYPE )

#-------------------------------------------------------------------------------
# Look for libraries we depend on
SET( OPENCV_VERSION 2.0.0 CACHE INTERNAL "OpenCV version requirement" FORCE )

IF ( PKG_CONFIG_FOUND )

    pkg_check_modules( OPENCV opencv>=${OPENCV_VERSION} )
    IF ( NOT OPENCV_FOUND )
        MESSAGE (SEND_ERROR "\nError: OpenCV version >=${OPENCV_VERSION} and development files not found.")
    ELSE ( NOT OPENCV_FOUND )

        SET( OPENCV_LIBRARY_PATH ${OPENCV_LIBRARY_DIRS} CACHE INTERNAL "OpenCV library path" )
        APPEND_LIBRARY_VARS_TO_CACHED_LISTS( ${OPENCV_INCLUDE_DIRS}
                                ${OPENCV_LIBRARY_DIRS}
                                ${OPENCV_LINK_LIBS}
                                ${OPENCV_LIBRARIES}
                                ${OPENCV_LDFLAGS} )
    ENDIF ( NOT OPENCV_FOUND )

ELSE ( PKG_CONFIG_FOUND )

  SET( BUILD_ROBOARDCONTROL OFF CACHE INTERNAL "Build RoBoardControl" FORCE )
  MESSAGE( FATAL_ERROR "\nError: pkg-config not found" )

ENDIF ( PKG_CONFIG_FOUND )

#-------------------------------------------------------------------------------
# Add in CxxTest unit tests
#ENABLE_TESTING()

# Use Python interpreter
#FIND_PACKAGE(PythonInterp)

#SET(CXXTESTGEN /home/abroun/dev/extra/cxxtest/cxxtestgen.py)
#
#ADD_CXXTEST( unitTests 
#            ${PROJECT_SOURCE_DIR}/unitTests/VectorTests.h
#            ${PROJECT_SOURCE_DIR}/unitTests/MathUtilsTests.h )

#-------------------------------------------------------------------------------
# Include the source files

INCLUDE_DIRECTORIES(
    ${PROJECT_SOURCE_DIR} 
    ${PROJECT_BINARY_DIR}
    /home/abroun/dev/extra/cxxtest
    ${PROJECT_SOURCE_DIR}/src
    ${global_include_dirs} )

ADD_SUBDIRECTORY( src )

MESSAGE( STATUS "Build Type: ${CMAKE_BUILD_TYPE}" )

