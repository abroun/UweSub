#-------------------------------------------------------------------------------
# Provides logging services for AUV control scripts
#-------------------------------------------------------------------------------

from __future__ import print_function

import os
import string
import sys
from datetime import datetime

#-------------------------------------------------------------------------------
class Logger:
    
    #---------------------------------------------------------------------------
    def __init__( self, config, logToFile = True ):
        
        self.logFileDir = string.Template( config.logFileDir ).safe_substitute( os.environ )
        self.logFilename = self.logFileDir + "/" + str( datetime.now() ) + ".log"
            
        if logToFile:
            self.outputFiles = [ open( self.logFilename, "w" ) ]
        else:
            self.outputFiles = []
    
    #---------------------------------------------------------------------------
    def addOutputFile( self, outputFile ):
        if not outputFile in self.outputFiles:
            self.outputFiles.append( outputFile )
            
    #---------------------------------------------------------------------------
    def addOutputToStdOut( self ):
        self.addOutputFile( sys.stdout )
            
    #---------------------------------------------------------------------------
    def logMsg( self, message ):
        
        timestampedMessage = str( datetime.now() ) + " - " + message
        for outputFile in self.outputFiles:
            print( timestampedMessage, file=outputFile )
        
    #---------------------------------------------------------------------------
    def logError( self, errorMessage ):
        
        self.logMsg( "ERROR - " + errorMessage )