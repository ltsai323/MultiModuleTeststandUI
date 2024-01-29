import paramiko
from tools.MesgHub import MesgEncoder
from tools.LogTool import LOG
#INDICATOR = 'SSHConnection'
#def MESG(mesg): return MesgEncoder(INDICATOR,mesg)
#def MERR(mesg): return MesgEncoder(INDICATOR, '[ERROR] '+mesg)

from dataclasses import dataclass
@dataclass
class ConnectionConfig:
    host:str
    port:int
    user:str
    pwd:str
    tag:str

class SingleConnector:
    def MESG(self,mesg): return MesgEncoder(self.config.tag, mesg)
    def MERR(self,mesg): return MesgEncoder(self.config.tag, '[ERROR] '+mesg)

    def SetConfig(self, connectCONFIG:ConnectionConfig):
        self.config = connectCONFIG
        self.stat = 0
        LOG('IgnoreWarning', '---', 'Warning "Blowfish has been deprecated" ignored')
    def Init(self):
        try:
            self.connection = paramiko.SSHClient()
            # Automatically add the server's host key (this is insecure, see comments below)
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the SSH server with AES encryption
            self.connection.connect(self.config.host, self.config.port, self.config.user, self.config.pwd)
            self.stat = 1
            LOG('CONNECTED', 'SingleConnector.Init', f'Connection Established to {self.config.user}@{self.config.host}')
        except Exception as e:
            print(f"Error: {e}")
            LOG('ERROR', 'Connection.Init', f'Connection to {self.config.user}@{self.config.host} failed')
            return self.MERR(f'Connection to {self.config.user}@{self.config.host} failed')
        return self.MESG(f'Connection Established to {self.config.user}@{self.config.host}')

    def SendCMD(self, theCMD):
        if self.stat != 1:
            LOG('ERROR', 'Connection.SendCMD', 'Connection Not initialized. Failed to send Command')
            return self.MERR('Connection Not initialized. Failed to send Command')

        # Execute the command
        stdin, stdout, stderr = self.connection.exec_command(theCMD)
        LOG('CMD Sent', 'SingleConnector.SendCMD', f'CMD: "{theCMD}" --- CMD Output: {stdout.read().decode()} --- CMD Error: {stderr.read().decode()}')
        return self.MESG(f'CMD sent: {theCMD}')
    def Close(self):
        if self.stat != 1:
            return self.MERR('No connection established.')
        self.connection.close()
        LOG('Closed', 'SingleConnector.Close', 'Safely close the connection')
        return self.MESG('Finished')



if __name__ == "__main__":
    # SSH server details
    # SSH server details
    host = "192.168.50.140"
    port = 22  # Default SSH port
    user = "ntucms"
    password = "9ol.1qaz5tgb"
    connConfig = ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password,
            tag = 'ControlPC',
            )
    conn = SingleConnector()
    conn.SetConfig(connConfig)
    conn.Init()
    conn.Close()
    #conn.ActivateDAQClient()
    #conn.SendCMD('cd V3HD_hexactrl && ls && ./run.sh TWH015_fixed')
    #conn.StopDAQClient()
