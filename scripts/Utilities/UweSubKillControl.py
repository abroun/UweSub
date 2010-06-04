#! /usr/bin/python

import socket
import paramiko
import sys
import getpass
from optparse import OptionParser

#-------------------------------------------------------------------------------
def runCommand( sshSession, command ):
    
    channel = sshConnection.open_session()
    channel.setblocking( 0 )

    channel.exec_command( command )
    channel.set_combine_stderr( True )        
    output = channel.makefile() 
 
    channel.recv_exit_status()
    channel.close()
    
    # Print the output
    for line in output:
        print line, # Comma added so that we don't get a new line

#-------------------------------------------------------------------------------
def runCommandInShell( sshSession, command ):
    
    channel = sshConnection.open_session()
    channel.setblocking( 0 )

    channel.get_pty( 'vt100',80,300 )
    channel.invoke_shell()
    channel.send( command )

    while not channel.recv_ready():
        pass

    channel.set_combine_stderr( True )        
    output = channel.makefile() 
 
    #channel.recv_exit_status()
    
    
    # Print the output
    line = output.readline()
    while line != None:
        print line, # Comma added so that we don't get a new line
        line = output.readline()
        
    channel.close()

#-------------------------------------------------------------------------------
def runCommandToString( sshSession, command ):
    
    channel = sshConnection.open_session()
    channel.setblocking( 0 )

    channel.exec_command( command )
    channel.set_combine_stderr( True )        
    output = channel.makefile() 
    
    channel.recv_exit_status()
    channel.close()
    
    outputString = ""
    for line in output:
        outputString += line
                
    return outputString


userName = "uwesub"
hostName = "192.168.8.10"

# Read in options from the command line
optionParser = OptionParser()
optionParser.add_option( "-u", "--username", dest="userName", help="Username on remote machine" )
optionParser.add_option( "-d", "--hostname", dest="hostName", help="Hostname of remote machine" )

(options, args) = optionParser.parse_args()

if options.userName != None:
    userName = options.userName

if options.hostName != None:
    hostName = options.hostName
        
# Connect to the remote machine
sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
sock.connect( ( hostName, 22 ) )

sshConnection = paramiko.Transport( sock )

sshConnection.start_client()
if not sshConnection.is_active():
    sshConnection.close()
    print "Error: Unable to connect"
    sys.exit( -1 )
 
authenticated = False
while not authenticated:
    password = getpass.getpass( "Please enter the password for " + userName + "@" + hostName + ": " )
    sshConnection.auth_password( userName, password )
    if not sshConnection.is_authenticated():
        print "Authentication failed"
    else:
        authenticated = True

# Do the work
runCommandInShell( sshConnection, "initctl list" )

#if runCommandToString( sshConnection, "sudo -n initctl list | grep -i \"UweSubControl start\"" ) != "":
#    runCommand( sshConnection, "sudo -n initctl stop UweSubControl" )
    
#if runCommandToString( sshConnection, "ls /etc/init/UweSubControl.conf" ) != "":
#    runCommand( sshConnection, "sudo -n mv /etc/init/UweSubControl.conf /etc/init/UweSubControl.conf.bak" )

# Clean up
sshConnection.close()

