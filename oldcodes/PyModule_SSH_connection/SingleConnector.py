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

def Initialized(singleCONNECTOR, showNOTinitWARNING:bool=False, funcNAME:str = ''):
    if hasattr(singleCONNECTOR, 'connection'): return True
    if showNOTinitWARNING:
        singleCONNECTOR.MESG('NotInitialized', f'No connection initialized, ignore process {funcNAME}')
    return False
class StatusMesg: # asdf
    stat_nothing = 0
    stat_idle = 1
    stat_busy = 2
    stat_bkgrun = 3
    stat_error = -1
    def __init__(self):
        self.new_stat = 'N/A'
        self.new_mesg = ''
        self.all_mesg = []
    def SetTaskEnding(self, mesg):
        self.SetIdle()
        self.new_mesg = mesg
        self.all_mesg.append(self.new_mesg)
    def SetTaskRunning(self, mesg):
        self.SetBusy()
        self.new_mesg = mesg
        self.all_mesg.append(self.new_mesg)

    def SetErrorMesg(self, errMESG):
        self.new_stat= StatusMesg.stat_error
        self.new_mesg = errMESG
        self.all_mesg.append(self.new_mesg)
    def SetBusy(self):
        self.new_stat = StatusMesg.stat_busy
    def SetBkgRunning(self):
        self.new_stat = StatusMesg.stat_bkgrun
    def SetIdle(self):
        self.new_stat = StatusMesg.stat_idle
    @property
    def IsBusy(self):
        return self.new_stat > StatusMesg.stat_busy
    @property
    def IsIdle(self):
        return self.new_stat == StatusMesg.stat_idle
    @property
    def IsError(self):
        return self.new_stat == StatusMesg.stat_error





class SingleConnector:
    def __init__(self, stdoutHANDLER=None, stderrHANDLER=None):
        self.the_stat = StatusMesg()
        if stdoutHANDLER and stderrHANDLER:
            self.set_logger(stdoutHANDLER,stderrHANDLER)
        self.terminate_flag = threading.Event()
        self.bkg_run_thread = None
    def MESG(self,stat,mesg): print(MesgHub.MesgUnitFactory(name='TestMesg', stat=stat,mesg=mesg))
    def MERR(self,stat,mesg): print(MesgHub.MesgUnitFactory(name='TestMesg', stat=stat,mesg='[ERROR] '+mesg))

    def SetConfig(self, connectCONFIG:ConnectionConfig):
        self.config = connectCONFIG
        self.MESG('IgnoreWarning', 'Warning "Blowfish has been deprecated" ignored')
    def set_logger(self, stdoutFUNC, stderrFUNC):
        self.MESG = stdoutFUNC
        self.MERR = stderrFUNC

    def Initialize(self):
        self.MESG('Initializing', f'SingleConnector.Initialize() : Building SSH connection to {self.config.host}:{self.config.port}')
        #self.the_stat.SetTaskRunning( myLOG('Initialize', 'SingleConnector.Init', 'Initialize SSH connection') )
        self.the_stat.SetBusy()
        if Initialized(self):
            self.MESG('Already Initialized', f'SingleConnector.Initialize() : SSH connection has been built. Use previous connection')
        else:
            try:
                self.connection = paramiko.SSHClient()
                # Automatically add the server's host key (this is insecure, see comments below)
                self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connect to the SSH server with AES encryption
                self.connection.connect(self.config.host, self.config.port, self.config.user, self.config.pwd)


                #new_shell.send('\x03') # ctrl + c
                self.MESG('Initialized', f'Successfully connected to {self.config.host}:{self.config.port}')
            except Exception as e:
                self.MERR('Failed Initialization', f'Connection to {self.config.host}:{self.config.port} failed.\n{e}')
        self.MESG('JOB_FINISHED', f'SSH connection to {self.config.host}:{self.config.port} is checked')
        self.the_stat.SetIdle()


    def send_cmd(self, theCMD):
        ''' Note:
                The code keeps reading stdout and send immediately.
                And if the code ended with error (using echo $?), the code start to send error message in one line.
        '''
        FUNC_NAME = '''SingleConnector.send_cmd()'''
        def _execute_command(self,bashCOMMAND):
            stdin, stdout, stderr = self.connection.exec_command(bashCOMMAND)

            endedStat = 0
            for line in stdout:
                if self.terminate_flag.is_set():
                    self.Close()
                    return

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
            # end of _execute_command()
        def _able_to_accept_cmd(self):
            FUNC_NAME = '''SingleConnector.send_cmd()'''

            if not Initialized(self,True, FUNC_NAME): return False
            if self.the_stat.IsBusy:
                myLOG('ForbidCMD', 'SingleConnector.SSH_ExecuteCMD()',f'command "{theCMD}" is ignored due to busy status')
                return False
            return True
            # end of _able_to_accept_cmd()

        if not _able_to_accept_cmd(self): return None
        self.the_stat.SetBusy()
        self.terminate_flag.clear()

        bash_command = theCMD + '; echo $?'
        self.bkg_thread = threading.Thread(target=_execute_command, args=(self,bash_command))
        self.bkg_thread.start()

    def Close(self):
        FUNC_NAME = '''SingleConnector.Close()'''
        self.the_stat.SetBusy()
        if Initialized(self):
            self.connection.close()
            self.the_stat.SetTaskEnding( myLOG('Closed', 'SingleConnector.Close', 'Safely close the connection') )
            self.MESG('SafelyClosed', f'{FUNC_NAME}: Safely closed a SSH connection from {self.config.host}:{self.config.port}')
            delattr(self, 'connection')
        else:
            self.the_stat.SetTaskEnding( myLOG('NoConnectionClosed', 'SingleConnector.Close', 'No connection established. Ignore "close" command') )
        self.the_stat.SetIdle()


JOBTYPE_WAIT = 'wait'
JOBTYPE_MONITOR = 'sent'
def SSH_ExecuteCMD(singleCONNECTOR:SingleConnector, theCMD, jobTYPE):
    FUNC_NAME = '''SingleConnector.SSH_ExecuteCMD()'''
    singleCONNECTOR.the_stat.SetTaskRunning( myLOG('Sending', FUNC_NAME, f'CMD "{theCMD}"') )
    singleCONNECTOR.send_cmd(theCMD)
    singleCONNECTOR.the_stat.SetBkgRunning()

def SSH_ForceStop(singleCONNECTOR:SingleConnector, theCMD:str=''):
    singleCONNECTOR.terminate_flag.set()
    singleCONNECTOR.the_stat.SetIdle()

    if theCMD != '':
        singleCONNECTOR.Initialize()
        SSH_ExecuteCMD(singleCONNECTOR, theCMD, JOBTYPE_WAIT)


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
    SSH_ExecuteCMD(conn,'echo hi sleeping for 5 second; sleep 5; echo ended', JOBTYPE_WAIT)
    SSH_ExecuteCMD(conn,'echo this line should not be executed ', JOBTYPE_WAIT)
    #SendCMDWithoutWaiting(conn,'ls && sh runGUI.sh LD myboardID 192.168.hi.jj;  sleep 5 && ls')
    #SendCMDWaitingForEnded(conn,'ls && sleep 5&& sh runGUI.sh LD myboardID 192.168.hi.jj&&  sleep 5 && ls')
    SSH_ForceStop(conn, 'echo closing process activated')
    SendCMDWaitingForEnded(conn,'echo this line should be executed in 5 seconds')
    print('sleeping for 10 sec')
    time.sleep(10)
    conn.Close()
    #conn.ActivateDAQClient()
    #conn.SendCMD('cd V3HD_hexactrl && ls && ./run.sh TWH015_fixed')
    #conn.StopDAQClient()
