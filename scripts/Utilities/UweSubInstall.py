#! /usr/bin/python

import socket
import paramiko
import sys
import os
import getpass
import string
from optparse import OptionParser
from sshConnection import sshConnection

# Please add files to be transfered to this list
# Environment variables can only be used in the source file names (left hand side)
FILE_TRANSFER_LIST = [
    # Libraries
    ( "${HOME}/dev/install/lib/uwesubplugin.so", "/home/uwesub/dev/install/lib/uwesubplugin.so" ),
    # Scripts
    ( "${HOME}/dev/uwe/UweSub/scripts/SubController.py", 
        "/home/uwesub/dev/uwe/UweSub/scripts/SubController.py" ),
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

# Substitute in environment variables
for i in range( len( FILE_TRANSFER_LIST ) ):
    srcTemplate = FILE_TRANSFER_LIST[ i ][ 0 ]
    FILE_TRANSFER_LIST[ i ] = \
        ( string.Template( FILE_TRANSFER_LIST[ i ][ 0 ] ).safe_substitute( os.environ ),
        FILE_TRANSFER_LIST[ i ][ 1 ] )

hostName = "192.168.8.10"

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

print "Restarting UweSubPlayer"
rootConnection.runCommand( "initctl start UweSubPlayer" )
