#! /usr/bin/python

import socket
import paramiko
import sys
import getpass
from optparse import OptionParser
from sshConnection import sshConnection

hostName = "192.168.8.10"

# Read in options from the command line
optionParser = OptionParser()
optionParser.add_option( "-d", "--hostname", dest="hostName", help="Hostname of remote machine" )

(options, args) = optionParser.parse_args()

if options.hostName != None:
    hostName = options.hostName
        
# Connect to the remote machine
rootConnection = sshConnection( hostName )

loggedOn = False
while not loggedOn:
    password = getpass.getpass( "Please enter the password for " + hostName + ": " )
    
    if not rootConnection.login( "root", password ):
        print "Authentication failed"
    else:
        loggedOn = True

print "Restoring UweSubControl.conf"
rootConnection.runCommand( "cp /etc/init/UweSubControl.conf.bak /etc/init/UweSubControl.conf" )
print "Starting UweSubControl"
rootConnection.runCommand( "initctl start UweSubControl" )
