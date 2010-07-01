#! /usr/bin/python

import socket
import paramiko
import sys
import os
import getpass
import string
import re
from optparse import OptionParser
from sshConnection import sshConnection

# Please add files to be transfered to this list
# Environment variables can only be used in the source file names (left hand side)
FILE_TRANSFER_LIST = [
    # UweSub Libraries
    ( "${HOME}/dev/install/lib/uwesubplugin.so", "/home/uwesub/dev/install/lib/uwesubplugin.so" ),
    # Player Libraries
   # ( "${HOME}/dev/install/lib/liblodo.so.3.0.1", "/home/uwesub/dev/install/lib/liblodo.so.3.0.1" ),
    #( "${HOME}/dev/install/lib/liblododriver.so.3.0.1", "/home/uwesub/dev/install/lib/liblododriver.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayerc.so.3.0.1", "/home/uwesub/dev/install/lib/libplayerc.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayerc++.so.3.0.1", "/home/uwesub/dev/install/lib/libplayerc++.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayercommon.so.3.0.1", "/home/uwesub/dev/install/lib/libplayercommon.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayercore.so.3.0.1", "/home/uwesub/dev/install/lib/libplayercore.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayerdrivers.so.3.0.1", "/home/uwesub/dev/install/lib/libplayerdrivers.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayerinterface.so.3.0.1", "/home/uwesub/dev/install/lib/libplayerinterface.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayerjpeg.so.3.0.1", "/home/uwesub/dev/install/lib/libplayerjpeg.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayertcp.so.3.0.1", "/home/uwesub/dev/install/lib/libplayertcp.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libplayerudp.so.3.0.1", "/home/uwesub/dev/install/lib/libplayerudp.so.3.0.1" ),
   # ( "${HOME}/dev/install/lib/libpmap.so.3.0.1", "/home/uwesub/dev/install/lib/libpmap.so.3.0.1" ),
    ( "${HOME}/dev/install/lib/libwavefront_standalone.so.3.0.1", "/home/uwesub/dev/install/lib/libwavefront_standalone.so.3.0.1" ),
    # Player Config files
    ( "${HOME}/dev/uwe/UweSub/data/PlayerConfigs/CompassTest.cfg", 
        "/home/uwesub/dev/uwe/UweSub/data/PlayerConfigs/CompassTest.cfg" ),
    ( "${HOME}/dev/uwe/UweSub/data/PlayerConfigs/DepthSensorTest.cfg", 
        "/home/uwesub/dev/uwe/UweSub/data/PlayerConfigs/DepthSensorTest.cfg" ),
    ( "${HOME}/dev/uwe/UweSub/data/PlayerConfigs/RealSub.cfg", 
        "/home/uwesub/dev/uwe/UweSub/data/PlayerConfigs/RealSub.cfg" ),
    ( "${HOME}/dev/uwe/UweSub/data/PlayerConfigs/SonarTest.cfg", 
        "/home/uwesub/dev/uwe/UweSub/data/PlayerConfigs/SonarTest.cfg" ),
    ( "${HOME}/dev/uwe/UweSub/data/PlayerConfigs/CompassTest.cfg", 
        "/home/uwesub/dev/uwe/UweSub/data/PlayerConfigs/CompassTest.cfg" ),
    # SubController Config files
    ( "${HOME}/dev/uwe/UweSub/data/SubControllerConfigs/RealWorld.cfg", 
        "/home/uwesub/dev/uwe/UweSub/data/SubControllerConfigs/RealWorld.cfg" ),
]

# Class for defining a directory transfer from a folder somewhere 
# in the HOME directory to the same directory in the HOME directory
# of the RoBoard
class HomeDirectoryTransfer:
    
    def __init__( self, relativeDir, filePatternList ):
        self.relativeDir = relativeDir
        self.filePatternList = filePatternList
        
DIRECTORY_TRANSFER_LIST = [ 
    HomeDirectoryTransfer( "dev/uwe/UweSub/scripts", [ ".+\.py$", ".+\.glade$" ] ) ]

SRC_HOME_DIR = string.Template( "${HOME}" ).safe_substitute( os.environ )
DST_HOME_DIR = "/home/uwesub"

# Substitute in environment variables
for i in range( len( FILE_TRANSFER_LIST ) ):
    srcTemplate = FILE_TRANSFER_LIST[ i ][ 0 ]
    FILE_TRANSFER_LIST[ i ] = \
        ( string.Template( FILE_TRANSFER_LIST[ i ][ 0 ] ).safe_substitute( os.environ ),
        FILE_TRANSFER_LIST[ i ][ 1 ] )

hostName = "192.168.8.11"

# Read in options from the command line
optionParser = OptionParser()
optionParser.add_option( "-d", "--hostname", dest="hostName", help="Hostname of remote machine" )

(options, args) = optionParser.parse_args()

if options.hostName != None:
    hostName = options.hostName
        
# Connect to the remote machine
rootConnection = sshConnection( hostName )      # Connection for restarting Player server
uwesubConnection = sshConnection( hostName )    # Connection for transferring files

loggedOn = False
while not loggedOn:
    password = getpass.getpass( "Please enter the password for " + hostName + ": " )
    
    if not rootConnection.login( "root", password ):
        print "Authentication failed"
    else:
        loggedOn = True
        
if not uwesubConnection.login( "uwesub", password ):
    print "Error: Unable to login as uwesub using the supplied password. " \
        + "It is assumed that the root and uwesub accounts have the same password"

if rootConnection.runCommandToString( "initctl list | /bin/grep -i \"UweSubPlayer start\"" ) != "":
    print "Stopping UweSubPlayer"
    rootConnection.runCommand( "initctl stop UweSubPlayer" )

print "Copying files"
sftpClient = uwesubConnection.openSFTPClient()
for ( src, dst ) in FILE_TRANSFER_LIST:
    print src
    sftpClient.put( src, dst )
    
for directoryTransfer in DIRECTORY_TRANSFER_LIST:
    srcDir = SRC_HOME_DIR + "/" + directoryTransfer.relativeDir
    patterns = [ re.compile( p ) for p in directoryTransfer.filePatternList ]
    
    for root, dirs, files in os.walk( srcDir ):
        dstRoot = re.sub( SRC_HOME_DIR, DST_HOME_DIR, root )
        for srcFile in files:
            
            matchFound = False
            for p in patterns:
                if p.match( srcFile ) != None:
                    matchFound = True
                    break
            
            if matchFound:
                dstFile = dstRoot + "/" + srcFile
                print srcFile
                sftpClient.put( srcFile, dstFile )

print "Restarting UweSubPlayer"
rootConnection.runCommand( "initctl start UweSubPlayer" )
