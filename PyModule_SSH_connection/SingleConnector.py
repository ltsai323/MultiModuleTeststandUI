import paramiko
from tools.MesgHub import MesgEncoder
import tools.MesgHub as MesgHub
from tools.LogTool import LOG
import threading
import time

from dataclasses import dataclass
@dataclass
class ConnectionConfig:
    host:str
    port:int
    user:str
    pwd:str


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

def Initialized(singleCONNECTOR):
    if hasattr(singleCONNECTOR, 'connection'): return True
    return False
class StatusMesg: # asdf
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
    def SetBusy(self):
        self.new_stat = 'busy'
    def SetBkgRunning(self):
        self.new_stat = 'bkgrunning'
    def SetIdle(self):
        self.new_stat = 'idle'




class SingleConnector:
    def __init__(self, stdoutHANDLER=None, stderrHANDLER=None):
        self.the_stat = StatusMesg()
        if stdoutHANDLER and stderrHANDLER:
            self.set_logger(stdoutHANDLER,stderrHANDLER)
    def MESG(self,stat,mesg): print(MesgHub.MesgUnitFactory(name='TestMesg', stat=stat,mesg=mesg))
    def MERR(self,stat,mesg): print(MesgHub.MesgUnitFactory(name='TestMesg', stat=stat,mesg='[ERROR] '+mesg))

    def SetConfig(self, connectCONFIG:ConnectionConfig):
        self.config = connectCONFIG
        self.stat = 0 # asdf del
        self.MESG('IgnoreWarning', 'Warning "Blowfish has been deprecated" ignored')
    def set_logger(self, stdoutFUNC, stderrFUNC):
        self.MESG = stdoutFUNC
        self.MERR = stderrFUNC

    def Initialize(self):
        self.MESG('Initializing', f'SingleConnector.Initialize() : Building SSH connection to {self.config.host}:{self.config.port}')
        #self.the_stat.SetTaskRunning( myLOG('Initialize', 'SingleConnector.Init', 'Initialize SSH connection') )
        self.the_stat.SetBusy()
        if Initialized(self):
            self.MESG('Already Initizlized', f'SingleConnector.Initialize() : SSH connection has been built. Use previous connection')
        else:
            try:
                self.connection = paramiko.SSHClient()
                # Automatically add the server's host key (this is insecure, see comments below)
                self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connect to the SSH server with AES encryption
                self.connection.connect(self.config.host, self.config.port, self.config.user, self.config.pwd)

                self.invokeShell = self.connection.invoke_shell()

                #new_shell.send('\x03') # ctrl + c
                self.MESG('Initialized', f'Successfully connected to {self.config.host}:{self.config.port}')
                self.stat = 1 # asdf del
            except Exception as e:
                self.stat = -1 # asdf del
                self.MERR('Failed Initialization', f'Connection to {self.config.host}:{self.config.port} failed.\n{e}')
        self.MESG('JOB_FINISHED', f'SSH connection to {self.config.host}:{self.config.port} is checked')
        self.the_stat.SetIdle()

    def send_cmd(self, theCMD):
        ''' Note:
                The code keeps reading stdout and send immediately.
                And if the code ended with error (using echo $?), the code start to send error message in one line.
        '''
        FUNC_NAME = '''SingleConnector.send_cmd()'''

        self.the_stat.SetBusy()
        if Initialized(self):
            bashCOMMAND = theCMD + '; echo $?'
            def execute_command(self,bashCOMMAND):
                print(f'testing : {bashCOMMAND}')
                stdin, stdout, stderr = self.connection.exec_command(bashCOMMAND)

                endedStat = 0
                for line in stdout:
                    the_mesg = line.strip()
                    self.MESG('LOG', the_mesg )
                    try:
                        ended_code = int(the_mesg)
                        endedStat = ended_code
                    except ValueError:
                        pass # ignore if the code is not an integer # this reqires the command send "echo $?" at the end of the command

                if endedStat != 0:
                    def all_errs(stderr):
                        yield f'Executing Command: "{bashCOMMAND}"'
                        for line in stderr:
                            yield line.strip()
                    self.MERR('ERROR FOUND', '\n'.join(all_errs(stderr) ) )
                self.MESG('JOB_FINISHED', f'end of command "{bashCOMMAND}"')

            bkgrun = threading.Thread(target=execute_command, args=(self,bashCOMMAND))
            bkgrun.start()
        return None
    def forceStop(self): # asdf currently this function do nothing for no reason
        if hasattr(self, 'invokeShell'):
            self.invokeShell.send('\x03')
            self.invokeShell.send('\003'.encode('ASCII'))
            self.invokeShell.send('\003')
            self.MESG('FORCE STOPPED', f'job has been stopped')
        else:
            self.MESG('Do NOthing', 'No job is running, so nothing happened with this FORCE STOP')


    def Close(self):
        FUNC_NAME = '''SingleConnector.Close()'''
        self.the_stat.SetBusy()
        if Initialized(self):
            self.connection.close()
            self.the_stat.SetTaskEnding( myLOG('Closed', 'SingleConnector.Close', 'Safely close the connection') )
            self.MESG('SafelyClosed', f'{FUNC_NAME}: Safely closed a SSH connection from {self.config.host}:{self.config.port}')
            delattr(self, 'connection')
            if hasattr(self, 'invokeShell') and self.invokeShell:
                delattr(self, 'invokeShell')
        else:
            self.the_stat.SetTaskEnding( myLOG('ERROR', 'SingleConnector.Close', 'No connection established. Ignore close command') )
        self.the_stat.SetIdle()

def SendCMDWaitingForEnded(singleCONNECTOR:SingleConnector, theCMD):
    FUNC_NAME = '''SingleConnector.SendCMDWaitingForEnded()'''
    singleCONNECTOR.the_stat.SetTaskRunning( myLOG('Sending', 'SingleConnector.SendCMD', f'Task running') )
    thread = singleCONNECTOR.send_cmd(theCMD)
    if thread: thread.join()

def SendCMDWithoutWaiting(singleCONNECTOR:SingleConnector, theCMD):
    singleCONNECTOR.the_stat.SetTaskRunning( myLOG('Sending', 'SingleConnector.SendCMDWithoutWaiting', f'Task running') )
    FUNC_NAME = '''SingleConnector.SendCMDWaitingForEnded()'''
    singleCONNECTOR.the_stat.SetTaskRunning( myLOG('Sending', 'SingleConnector.SendCMD', f'Task running') )
    thread = singleCONNECTOR.send_cmd(theCMD)
    singleCONNECTOR.the_stat.SetBkgRunning()


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
            )
    conn = SingleConnector()
    conn.SetConfig(connConfig)
    conn.Initialize()
    #SendCMD(conn,'ls')
    #SendCMDWithoutWaiting(conn,'ls && sh runGUI.sh LD myboardID 192.168.hi.jj;  sleep 5 && ls')
    #SendCMDWithoutWaiting(conn,'ls && sh runGUI.sh LD myboardID 192.168.hi.jj;  sleep 5 && ls')
    #SendCMDWaitingForEnded(conn,'ls && sleep 5&& sh runGUI.sh LD myboardID 192.168.hi.jj&&  sleep 5 && ls')
    SendCMDWaitingForEnded(conn,'ls 1>&2')
    conn.forceStop() # currently this function do nothing for no reason
    print('sleeping for 10 sec')
    time.sleep(10)
    conn.Close()
    #conn.ActivateDAQClient()
    #conn.SendCMD('cd V3HD_hexactrl && ls && ./run.sh TWH015_fixed')
    #conn.StopDAQClient()
