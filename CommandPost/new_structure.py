#!/usr/bin/env python3
from subunit import PyModuleConnectionConfig, SubUnit,PyModuleCommandPool
from subunit import PyModuleConnectionConfig
import tools.MesgHub as MesgHub
import socket
import threading
import errno
import sys
import time
TIMEOUT = 2.0
MAX_MESG_LENG = 1024
LOG_LEVEL = 5
def BUG(*mesg):
    if LOG_LEVEL < 1:
        print('#DEBUG# ', mesg)
def LOG(info,name,mesg):
    if LOG_LEVEL < 2:
        print(f'[{info} - LOG] (new_structure-{name}) {mesg}', file=sys.stderr)
def WARNING(info,name,mesg):
    if LOG_LEVEL < 4:
        print(f'[{info} - WARNING] (new_structure-{name}) {mesg}', file=sys.stderr)

STAT_N_A = 0
STAT_INITIALIZED = 1
STAT_CONNECTED = 2
STAT_CONFIGURED = 3
STAT_JOB_RUNNING = 4
STAT_JOB_FINISHED = 5

STAT_ERROR = -1
class UnitStatus:
    def __init__(self):
        self.status = STAT_N_A

    def check_status(self, statCODE):
        if self.status < statCODE: return False
        return True
    def IsInitialized(self):
        return self.check_status(STAT_INITIALIZED)
    def IsConnected(self):
        return self.check_status(STAT_CONNECTED)
    def IsConfigured(self):
        return self.check_status(STAT_CONFIGURED)



    def set_status(self, statCODE):
        self.status = statCODE
    def SetInitialized(self):
        self.set_status(STAT_INITIALIZED)
    def SetConnected(self):
        self.set_status(STAT_CONNECTED)
    def SetConfigured(self):
        self.set_status(STAT_CONFIGURED)
    def SetDestroyed(self):
        self.set_status(STAT_N_A)
    def SetError(self):
        self.set_status(STAT_ERROR)


def socket_error_handler(self, theCMD:str, socketFUNC) -> int:
    # return a status code
    self.unit_status.set_status(STAT_JOB_RUNNING)
    if not hasattr(self, 'socket_client'):
        WARNING('Ignore Command', self.name, 'UnitStageCommander::socket_error_handler() - PyModule "{self.name}" is not initialized')
        return STAT_N_A
    try:
        return socketFUNC(self,theCMD)
    except socket.error as e:
        err_mesg = ''
        if   e.errno == errno.ECONNREFUSED:
            err_mesg = 'Client connection refused'
        elif e.errno == errno.EHOSTUNREACH:
            err_mesg = 'Host Unreachable'
        else:
            err_mesg = f'Socket error : {e}'
        raise IOError(err_mesg)
def SendLongCMD(self, theCMD:str, theARG:str='' ) -> int:
    def long_cmd(self, theCMD):
        the_cmd = MesgHub.CMDUnitFactory(name=self.name, cmd = theCMD, arg=theARG)
        self.socket_client.sendall( MesgHub.SendSingleMesg(the_cmd) )
        BUG(f'sending cmd {the_cmd} ')
        while True:
            try:
                data = self.socket_client.recv(MAX_MESG_LENG)

                if not data or data == b'': continue
                rec_data = MesgHub.GetSingleMesg(data)
                self.record_message(rec_data)
                if rec_data.stat == 'JOB_FINISHED':
                    return STAT_JOB_FINISHED # close this connection
            except socket.timeout:
                continue # totally disable the timeout message. Such that all message comes from the running message
    return socket_error_handler(self,theCMD, long_cmd)
def SendShortCMD(self, theCMD:str) -> int:
    def short_cmd(self, theCMD):
        the_cmd = MesgHub.CMDUnitFactory(name=self.name, cmd = theCMD)
        print(f'the_cmd is {the_cmd}')
        self.socket_client.sendall( MesgHub.SendSingleMesg(the_cmd) )
        while True:
            try:
                data = self.socket_client.recv(MAX_MESG_LENG)

                if not data or data == b'': continue
                rec_data = MesgHub.GetSingleMesg(data)
                self.record_message(rec_data)
                return rec_data.stat
            except socket.timeout:
                continue # totally disable the timeout message. Such that all message comes from the running message
    return socket_error_handler(self,theCMD, short_cmd)
### Unit stage provides the staged command for further use.
### All PyModule must have these staged command in
### * Initialize  * Connect  * Configure  * Start  * Stop  * Distroy
### *** Running are not in the list.
from collections import deque
_MAX_LOG_TO_SHOW_ = 10

def BookExternalFunc(logMETHOD=None, sleepFUNC=None):
    def default_log_method(mesgUNIT:MesgHub.MesgUnit):
        LOG('TESTING', 'default_name', f'recording message from UnitStageCommander {mesgUNIT}')
    def default_sleep_func(sleepPERIOD):
        import time
        time.sleep(sleepPERIOD)
    log_method = logMETHOD if logMETHOD else default_log_method
    sleep_func = sleepFUNC if sleepFUNC else default_sleep_func
    return (log_method, sleep_func)

class UnitStageCommander:
    def __init__(self, subUNIT:SubUnit, logMETHOD = None, sleepFUNC = None):
        self.name = subUNIT.name
        self.unit_setup = subUNIT
        self.unit_status = UnitStatus()
        self.logs = deque(maxlen=_MAX_LOG_TO_SHOW_)
        self.log_func, self.sleep_func = BookExternalFunc(logMETHOD,sleepFUNC)

    def record_message(self, mesg):
        self.log_func(mesg)
        ### asdf
        ### to do 
        ###   a log file for output
        self.logs.append(mesg)
    @property
    def mesg(self):
        return self.logs[-1] if len(self.logs)>0 else MesgHub.MesgUnitFactory(name=self.name, stat='N/A', mesg='Not initialized')

    def LoadConfigProfile(self):
        return (self.name, self.unit_setup.ConfigDict)



    def Initialize(self):
        if hasattr(self, 'socket_client'):
            WARNING('Ignore Command', self.name, f'UnitStageCommander::Initialize() - The communication to PyModule "{self.name}" was built. Ignore this initialization')
            return
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_client.connect( (self.unit_setup.connect_config.addr,self.unit_setup.connect_config.port) )
        self.unit_status.SetInitialized()
        self.socket_client.settimeout(TIMEOUT)

        LOG('Initialized', self.name, f'UnitStageCommander::Initialize() - Communication to PyModule "{self.name}" is built successfully.')
    def Connect(self):
        for serialized_cmd in SerializedCMDs(self, 'CONNECT'):
            SendLongCMD(self, serialized_cmd['cmd'], self.unit_setup.connect_config.name)
            self.sleep_func(serialized_cmd['timegap'])

        LOG('Connected', self.name, f'UnitStageCommander::Connect() - PyModule "{self.name}" successfully connected to hardware.')
    def Configure(self):
        for serialized_cmd in SerializedCMDs(self, 'CONFIGURE'):
            SendLongCMD(self, serialized_cmd['cmd'], self.unit_setup.AllConfigsAsUpdateArg() )
            self.sleep_func(serialized_cmd['timegap'])
    def Run(self):
        for serialized_cmd in SerializedCMDs(self, 'RUN'):
            SendLongCMD(self, serialized_cmd['cmd'])
            self.sleep_func(serialized_cmd['timegap'])

    def Destroy(self):
        ''' need to destroy socket_client '''
        for serialized_cmd in SerializedCMDs(self, 'DESTROY'):
            SendLongCMD(self, serialized_cmd['cmd'])
            self.sleep_func(serialized_cmd['timegap'])
    def Test(self):
        SendLongCMD(self, 'test')
        LOG('testing', self.name, f'UnitStageCommander::Test() - Connection destroyed to PyModule "{self.name}".')

''' Every SendLongCMD is required to load the commands inside yaml file '''
''' Need to load configuration profiles at initialize or connect step asdf '''
def SerializedCMDs(unitstageCMDer: UnitStageCommander, theCMD:str):
    cmd_pool = unitstageCMDer.unit_setup.cmd_pool.sys_cmds
    if theCMD not in cmd_pool:
        raise IOError(f'Input command "{theCMD}" does not recognized in available system commands "{cmd_pool.keys()}"')
    serialized_cmds = cmd_pool[theCMD]

    def out_format(cmdSTR:str,waitingFOR:float):
        return { 'cmd':cmdSTR, 'timegap': waitingFOR }
    return [ out_format(serialized_cmd['cmd'],serialized_cmd['timegap']) for serialized_cmd in serialized_cmds ]


class CommandPost:
    def __init__(self, *subUNITs):
        duplicate_connect_config_checking( (unit.connect_config for unit in subUNITs) )
        self.subunits = { unit.name:unit for unit in subUNITs }






if __name__ == "__main__":

    pwrconn = PyModuleConnectionConfig('PWR1', '192.168.50.60', 2000)
    pwrconf = PyModuleCommandPool('data/subunit_testsample.yaml')
    pwrunit = SubUnit(pwrconn,pwrconf)

    #print(pwrunit.cmd_pool.GetConfig('volt'))
    #pwrunit.Help()
    #print(pwrunit.CommandList)

    def log_method(mesgUNIT:MesgHub.MesgUnit):
        print(f'recording message from UnitStageCommander {mesgUNIT}')
    pwrcmder = UnitStageCommander(pwrunit, log_method)
    pwrcmder.Initialize()
    pwrcmder.Connect()
    pwrcmder.Destroy()

