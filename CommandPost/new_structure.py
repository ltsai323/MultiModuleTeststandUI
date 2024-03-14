#!/usr/bin/env python3
from subunit import PyModuleConnectionConfig, SubUnit,PyModuleCommandPool
from subunit import PyModuleConnectionConfig
import tools.MesgHub as MesgHub
import socket
import threading
import errno
import sys
TIMEOUT = 2.0
MAX_MESG_LENG = 1024
LOG_LEVEL = 1
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
class UnitStageCommander:
    def __init__(self, subUNIT:SubUnit):
        self.name = subUNIT.name
        self.unit_setup = subUNIT
        self.unit_status = UnitStatus()
        self.logs = deque(maxlen=_MAX_LOG_TO_SHOW_)

    def record_message(self, mesg):
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
        SendLongCMD(self, 'connect', self.unit_setup.connect_config.name) # Set the module name

        LOG('Connected', self.name, f'UnitStageCommander::Connect() - PyModule "{self.name}" successfully connected to hardware.')
    def Configure(self):
        SendLongCMD(self,'UPDATE', self.unit_setup.AllConfigsAsUpdateArg() )
        #SendLongCMD(self,'on')
    def Run(self):
        SendLongCMD(self, 'set')
        SendLongCMD(self, 'on')

    def Destroy(self):
        SendLongCMD(self,'DESTROY')
        LOG('Destroyed', self.name, f'UnitStageCommander::Destroy() - Connection destroyed to PyModule "{self.name}".')
        ''' need to destroy socket_client '''
    def Test(self):
        SendLongCMD(self, 'test')
        LOG('testing', self.name, f'UnitStageCommander::Test() - Connection destroyed to PyModule "{self.name}".')

''' Every SendLongCMD is required to load the commands inside yaml file '''
''' Need to load configuration profiles at initialize or connect step asdf '''


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

    pwrcmder = UnitStageCommander(pwrunit)
    pwrcmder.Initialize()
    pwrcmder.Connect()
    pwrcmder.Connect()
    pwrcmder.Destroy()

