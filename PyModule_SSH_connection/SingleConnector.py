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


@dataclass
class LogObj:
    title:str
    source:str
    mesg:str
    def __str__(self):
        return f'[{self.title} - ({self.source})] {self.mesg}'
def myLOG(arg1,arg2,arg3):
    LOG(arg1,arg2,arg3)
    return LogObj(arg1,arg2,arg3)

class StatusMesg:
    def __init__(self):
        self.new_stat = 'N/A'
        self.new_mesg = ''
        self.all_mesg = []
    def SetTaskEnding(self, mesg):
        self.new_stat = 'taskend'
        self.new_mesg = mesg
        self.all_mesg.append(self.new_mesg)
    def SetTaskRunning(self, mesg):
        self.new_stat = 'running'
        self.new_mesg = mesg
        self.all_mesg.append(self.new_mesg)

    def SetErrorMesg(self, errMESG):
        self.new_stat= 'error'
        self.new_mesg = errMESG
        self.all_mesg.append(self.new_mesg)
def GetMesg(statusMESG):
    if statusMESG.new_stat == 'pending':
        return { 'stat': 'pending' }
    if statusMESG.new_stat == 'taskend':
        statusMESG.new_stat = 'pending'
        return { 'stat': 'taskend', 'mesg':str(statusMESG.new_mesg) }

    if statusMESG.new_stat == 'running':
        if statusMESG.new_mesg != '':
            mesg = statusMESG.new_mesg
            statusMESG.new_mesg = ''
            return { 'stat': 'running', 'mesg':str(mesg) }
        return {'stat': 'running'}
    if statusMESG.new_stat == 'error':
        if statusMESG.new_mesg != '':
            mesg = statusMESG.new_mesg
            statusMESG.new_mesg = ''
            return { 'stat': 'error', 'mesg':str(mesg) }
        return {'stat': 'error'}




class SingleConnector:
    def __init__(self):
        self.the_stat = StatusMesg()
    def MESG(self,mesg): return MesgEncoder(self.config.tag, mesg)
    def MERR(self,mesg): return MesgEncoder(self.config.tag, '[ERROR] '+mesg)

    def SetConfig(self, connectCONFIG:ConnectionConfig):
        self.config = connectCONFIG
        self.stat = 0
        LOG('IgnoreWarning', '---', 'Warning "Blowfish has been deprecated" ignored')
    def Init(self):
        self.the_stat.SetTaskRunning( myLOG('Init', 'SingleConnector.Init', 'Initialize SSH connection') )
        try:
            self.connection = paramiko.SSHClient()
            # Automatically add the server's host key (this is insecure, see comments below)
            self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the SSH server with AES encryption
            self.the_stat.SetTaskRunning( myLOG('Conn', 'SingleConnector.Init', f'Connecting to {self.config.host}@{self.config.port}') )
            self.connection.connect(self.config.host, self.config.port, self.config.user, self.config.pwd)
            self.stat = 1
        except Exception as e:
            print(f"Error: {e}")
            self.the_stat.SetErrorMesg( myLOG('ERROR', 'Connection.Init', f'Connection to {self.config.user}@{self.config.host} failed') )
            return self.MERR(f'Connection to {self.config.user}@{self.config.host} failed')

        self.the_stat.SetTaskEnding( myLOG('CONNECTED', 'SingleConnector.Init', f'Connection Established to {self.config.user}@{self.config.host}') )
        return self.MESG(f'Connection Established to {self.config.user}@{self.config.host}')

    def SendCMD(self, theCMD):
        self.the_stat.SetTaskRunning( myLOG('Sending', 'SingleConnector.SendCMD', f'Task running') )
        if self.stat != 1:
            self.the_stat.SetErrorMesg( myLOG('ERROR', 'SingleConnector.SendCMD', 'Connection Not initialized. Failed to send Command') )

            return self.MERR('Connection Not initialized. Failed to send Command')

        # Execute the command
        stdin, stdout, stderr = self.connection.exec_command(theCMD)

        self.the_stat.SetTaskEnding( myLOG('CMD Sent', 'SingleConnector.SendCMD', f'CMD: {theCMD} --- CMD Output: {stdout.read().decode()}') )
        return self.MESG( str(GetMesg(self.the_stat)) )
        #return self.MESG(f'CMD sent: {theCMD}')
    def Close(self):
        if self.stat != 1:
            self.the_stat.SetTaskEnding( myLOG('ERROR', 'SingleConnector.Close', 'No connection established. Ignore close command') )
            return self.MERR('No connection established.')
        self.connection.close()
        self.the_stat.SetTaskEnding( myLOG('Closed', 'SingleConnector.Close', 'Safely close the connection') )
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
