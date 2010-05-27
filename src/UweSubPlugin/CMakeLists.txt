#-------------------------------------------------------------------------------
INCLUDE( ${PROJECT_SOURCE_DIR}/cmake/utils.cmake )

#-------------------------------------------------------------------------------
# Include all the search paths for headers
INCLUDE_DIRECTORIES(
    .
    ${global_include_dirs}
    ${PROJECT_SOURCE_DIR}/3rdParty/Roboard/Include )

SET( srcFiles 
    UweSubPlugin.cpp
    MotorDriver.cpp )

LINK_DIRECTORIES( 
    ${global_link_dirs}
    ${PROJECT_SOURCE_DIR}/3rdParty/Roboard/Lib )

ADD_LIBRARY( uwesubplugin SHARED ${srcFiles} )
SET_TARGET_PROPERTIES( uwesubplugin PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR} )
# delete the "lib" prefix from the plugin
SET_TARGET_PROPERTIES( uwesubplugin PROPERTIES PREFIX "" )

TARGET_LINK_LIBRARIES( uwesubplugin
    ${global_link_libs}
     RBIO )

INSTALL( TARGETS uwesubplugin
        LIBRARY DESTINATION lib )
