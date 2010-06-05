
import socket
import paramiko

class sshConnection():
    
    #---------------------------------------------------------------------------
    def __init__( self, host, port = 22 ):
        
        # Connect to the remote machine
        self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.socket.connect( ( host, port ) )

        self.transport = paramiko.Transport( self.socket )

        self.transport.start_client()
        if not self.transport.is_active():
            self.transport.close()
            raise Exception( "Unable to connect" )
        
    #---------------------------------------------------------------------------
    def login( self, userName, password ):
        
        self.transport.auth_password( userName, password )
        if not self.transport.is_authenticated():
            return False
        else:
            return True
            
    #---------------------------------------------------------------------------
    def openSFTPClient( self ):
        return self.transport.open_sftp_client()
        
    #-------------------------------------------------------------------------------
    def runCommand( self, command ):
        
        channel = self.transport.open_session()
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
    def runCommandToString( self, command ):
        
        channel = self.transport.open_session()
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