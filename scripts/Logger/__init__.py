#-------------------------------------------------------------------------------
# Provides logging services for AUV control scripts
#-------------------------------------------------------------------------------

import os
import string
import sys
from datetime import datetime

#-------------------------------------------------------------------------------
class Logger:
    
    #---------------------------------------------------------------------------
    def __init__( self, config ):
        
        self.logFileDir = string.Template( config.logFileDir ).safe_substitute( os.environ )
        self.logFilename = self.logFileDir + "/" + datetime.now() + ".log"
            
        self.outputFiles = [ open( self.logFilename ) ]
        pass
    
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