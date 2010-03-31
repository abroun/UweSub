IF ( ENABLE_PYTHON )

    INCLUDE_DIRECTORIES(
        .
        ${PYTHON_INCLUDE_PATH}
        ${global_include_dirs}
        ${PROJECT_SOURCE_DIR}/3rdParty/sba )

    SET( srcFiles 
        RoBoardControl.cpp )

    SET_SOURCE_FILES_PROPERTIES( ${srcFiles} 
        PROPERTIES COMPILE_FLAGS "-pthread -fno-strict-aliasing -fwrapv -fPIC" )

    LINK_DIRECTORIES( 
        ${global_link_dirs}
        ${PROJECT_SOURCE_DIR}/3rdParty/sba )
    ADD_LIBRARY( PythonRoBoardControl SHARED ${srcFiles} )
    SET_TARGET_PROPERTIES( PythonRoBoardControl PROPERTIES OUTPUT_NAME "RoBoardControl" )

    # delete the "lib" prefix from the library
    SET_TARGET_PROPERTIES( PythonRoBoardControl PROPERTIES PREFIX "" )

    SET_TARGET_PROPERTIES( PythonRoBoardControl PROPERTIES INSTALL_NAME_DIR "${PYTHON_INSTDIR}" )

    SET_TARGET_PROPERTIES( PythonRoBoardControl 
        PROPERTIES LINK_FLAGS "-pthread -Wl,-O1 -Wl,-Bsymbolic-functions" )

    TARGET_LINK_LIBRARIES( PythonRoBoardControl 
        ColourTracker
        ${global_link_libs}
        sba
        lapack
        blas
        libf2c.a
        m )

    INSTALL( TARGETS PythonRoBoardControl
        LIBRARY DESTINATION ${PYTHON_INSTDIR} )

ENDIF( ENABLE_PYTHON )

