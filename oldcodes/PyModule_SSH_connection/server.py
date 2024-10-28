from dataclasses import dataclass
#from SingleConnector import SingleConnector, ConnectionConfig
import SingleConnector
from tools.LogTool import LOG

import tools.SocketProtocol_ as SocketProtocol
import tools.MesgHub as MesgHub
import time
import re

AVAILABLE_SOCKET_COMMANDS = {
        'connect': 'connect',
        'configure': 'UPDATE',
        'run'    : 'run',
        'stop'   : 'stop',
        'destroy': 'DESTROY',

        'test'   : 'test',
        }
AVAILABVLE_CMD_TYPES = {
        'skip': 'do_nothing',
        'wait': 'waiting_for_job_ended',     # only wait and sent will be sent to SingleConnector
        'sent': 'job_sent_without_waiting',

        'kill': 'abort_current_ssh_session',
        'read': 'monitor_output', # keep reading the output
        }
JOB_FINISHED=0
JOB_IS_RUNNING=1

def run_cmd_with_type(theCONFIGs:SocketProtocol.RunningConfigurations, remoteCMDset):
    jobTYPE = remoteCMDset.get('type','sent')
    waitTIM = remoteCMDset['delay']
    cmdCONT = remoteCMDset.get('cmd','')
    job_stat = JOB_FINISHED
    if jobTYPE == AVAILABVLE_CMD_TYPES['skip']: pass
    if jobTYPE == AVAILABVLE_CMD_TYPES['wait']:
        send_ssh_mesg(theCONFIGs, full_CMD_with_args(theCONFIGs, cmdCONT), jobTYPE)
        job_stat = JOB_IS_RUNNING
    if jobTYPE == AVAILABVLE_CMD_TYPES['sent']:
        send_ssh_mesg(theCONFIGs, full_CMD_with_args(theCONFIGs, cmdCONT), jobTYPE)
    if jobTYPE == AVAILABVLE_CMD_TYPES['kill']:
        theCONFIGs.connMgr.Close() # no matter the command executed or not. Destroy the connection instance in python.
        theCONFIGs.MESG('KillSSHSession', 'abort from current SSH connection')
    if jobTYPE == AVAILABVLE_CMD_TYPES['read']:
        keep_reading_output_message(theCONFIGs)

    time.sleep(waitTIM)
    return job_stat

class CMDConnect:
    remote_cmd = AVAILABLE_SOCKET_COMMANDS['connect']
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool: # true: 
        theCONFIGs.name = self.cmd_unit.name
        theCONFIGs.MESG('NameUpdated', f'PyModule name is set from remote "{theCONFIGs.name}"')
        theCONFIGs.connMgr.Initialize()
        return JOB_FINISHED
class CMDDestroy:
    remote_cmd = AVAILABLE_SOCKET_COMMANDS['destroy']
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        time.sleep(1.0)
        remote_cmd_set = theCONFIGs.destroyCMD
        job_stat = run_cmd_with_type(theCONFIGs,theCONFIGs.destroyCMD)
        theCONFIGs.connMgr.Close() # no matter the command executed or not. Destroy the connection instance in python.
        return job_stat
class CMDRun:
    remote_cmd = AVAILABLE_SOCKET_COMMANDS['run']
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        job_stat = run_cmd_with_type(theCONFIGs,theCONFIGs.runCMD    )
        return job_stat


class CMDStop:
    remote_cmd = AVAILABLE_SOCKET_COMMANDS['stop']
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        job_stat = run_cmd_with_type(theCONFIGs,theCONFIGs.stopCMD   )
        return job_stat
class CMDTest:
    remote_cmd = AVAILABLE_SOCKET_COMMANDS['test']
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        job_stat = run_cmd_with_type(theCONFIGs,theCONFIGs.testCMD   )
        return job_stat

class CMDConfigure:
    remote_cmd = AVAILABLE_SOCKET_COMMANDS['configure']
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        'aaa:3.14|bbb:6.28|ccc:7.19'
        theCONFIGs.SetValues(self.cmd_unit.arg)
        theCONFIGs.MESG('ConfigUpdated', f'Update configuration {self.cmd_unit.arg}')

        return JOB_FINISHED
def CMDInstanceFactory(cmdUNIT:MesgHub.CMDUnit):
    if cmdUNIT.cmd == CMDConnect.remote_cmd:
        return CMDConnect(cmdUNIT)
    if cmdUNIT.cmd == CMDDestroy.remote_cmd:
        return CMDDestroy(cmdUNIT)
    if cmdUNIT.cmd == CMDRun.remote_cmd:
        return CMDRun(cmdUNIT)
    if cmdUNIT.cmd == CMDStop.remote_cmd:
        return CMDStop(cmdUNIT)
    if cmdUNIT.cmd == CMDTest.remote_cmd:
        return CMDTest(cmdUNIT)
    if cmdUNIT.cmd == CMDConfigure.remote_cmd:
        return CMDConfigure(cmdUNIT)
@dataclass
class Configurations:
    name:str

def full_CMD_with_args(theCONFIGs:SocketProtocol.RunningConfigurations, cmdSTR:str) -> str:
    used_var_names = lambda cmdFRAGMENT: re.findall( r'{([^{}]+)}', cmdFRAGMENT)
    variable_names = used_var_names(cmdSTR)
    loaded_variables = { name:getattr(theCONFIGs,name) for name in variable_names }
    return cmdSTR.format(**loaded_variables)

def send_ssh_mesg(theCONFIGs:SocketProtocol.RunningConfigurations,bashCMD:str, jobTYPE:str):
    if not hasattr(theCONFIGs.connMgr,'connection'): # connection = paramiko.SSHClient()
        theCONFIGs.MESG('NotInitializedError', f'SingleConnector was not connected to any SSH server. Initialize before send any message. cmd[{bashCMD}]')
        return 'nothing send to HW'
    return SingleConnector.SSH_ExecuteCMD(theCONFIGs.connMgr,bashCMD, jobTYPE)

def main_func(theCONFIGs:SocketProtocol.RunningConfigurations,command:MesgHub.CMDUnit):
    theCONFIGs.MESG('CMD Received', command.cmd)


    mesg_box = ''
    exec_unit = CMDInstanceFactory(command)
    if exec_unit:
        job_stat = exec_unit.execute(theCONFIGs)
        if job_stat == JOB_FINISHED:
            theCONFIGs.MESG('JOB_FINISHED', f'running cmd {command.cmd}') # Notify the execution is finished.
            theCONFIGs.module_status = SocketProtocol.MODULE_STATUS['idle']
    else:
        theCONFIGs.MERR('CMD_NOT_FOUND', f'input CMD : "{command.cmd}" is an invalid command.')

def communicate_with_socket(socketPROFILE:SocketProtocol.SocketProfile, clientSOCKET,command:MesgHub.CMDUnit):

    def log(theSTAT:str,theMESG:str):
        LOG(theSTAT, 'execute_command', theMESG)
        SocketProtocol.UpdateMesgAndSend( socketPROFILE, clientSOCKET, theSTAT, theMESG)
    def err(theSTAT:str,theMESG:str):
        LOG(theSTAT, 'error_found', theMESG)
        SocketProtocol.UpdateMesgAndSend( socketPROFILE, clientSOCKET, theSTAT, theMESG)

    configs = socketPROFILE.configs
    configs.MESG = log
    configs.MERR = err
    configs.connMgr.set_logger(log,err)


    main_func(configs, command)
def TestFunc_WithoutSocketConnection():
    # control PC
    from tools.YamlHandler import YamlLoader
    inputFILE='config/sshconfigs.commanderPC.daqClient.yaml'
    loadedCONFIGs = YamlLoader(inputFILE)

    default_configs = SingleConnector.ConnectionConfig(
            host = loadedCONFIGs.configs['host'],
            port = loadedCONFIGs.configs['port'],
            user = loadedCONFIGs.configs['user'],
            pwd = loadedCONFIGs.configs['password'],
            )

    # new
    def log(theSTAT:str,theMESG:str):
        LOG(theSTAT, '- TESTING -', theMESG)
    def err(theSTAT:str,theMESG:str):
        LOG(theSTAT, '- _ERROR_ -', theMESG)

    LOG('Service Activated', 'SSHConnection',f'Activate Socket@0.0.0.0:2000')
    LOG('Service Activated', 'SSHConnection',f'Connecting to {default_configs.host}:{default_configs.port} via SSH')
    run_configs = SocketProtocol.RunningConfigurations(log)
    run_configs.SetDefault(loadedCONFIGs)
    '''
    for argNAME, arg in loadedCONFIGs.configs.items():
        setattr(run_configs,argNAME,arg)
    '''
    run_configs.MESG = log
    setattr(run_configs, 'connMgr', SingleConnector.SingleConnector(log,err) )
    run_configs.connMgr.SetConfig(default_configs)

    import time
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='connect')
    main_func(run_configs, socketCMD)
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='test')
    main_func(run_configs, socketCMD)
    print('------------ rejecting job ------------')
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='test') # should reject this command
    main_func(run_configs, socketCMD)
    print('------------ job rejected ------------')
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='stop') # should terminate previous command
    main_func(run_configs, socketCMD)
    print('------------ job stopped ------------')
    time.sleep(5)
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='DESTROY')
    print('TestFunc() middle term')
    main_func(run_configs, socketCMD)

    print('TestFunc() Finished')
    exit()

if __name__ == "__main__":
    #TestFunc_WithoutSocketConnection()
    from tools.YamlHandler import YamlLoader
    import sys
    inputFILE=sys.argv[1]
    loadedCONFIGs = YamlLoader(inputFILE)

    default_configs = SingleConnector.ConnectionConfig(
            host = loadedCONFIGs.configs['host'],
            port = loadedCONFIGs.configs['port'],
            user = loadedCONFIGs.configs['user'],
            pwd = loadedCONFIGs.configs['password'],
            )




    # new
    LOG('Service Activated', 'SSHConnection',f'Activate Socket@0.0.0.0:2000')
    LOG('Service Activated', 'SSHConnection',f'Connecting to {default_configs.host}:{default_configs.port} via SSH')
    run_configs = SocketProtocol.RunningConfigurations()
    run_configs.SetDefault(loadedCONFIGs)
    '''
    for argNAME, arg in loadedCONFIGs.configs.items():
        setattr(run_configs,argNAME,arg)
    '''
    setattr(run_configs, 'connMgr', SingleConnector.SingleConnector() )
    run_configs.connMgr.SetConfig(default_configs)

    connection_profile = SocketProtocol.SocketProfile(communicate_with_socket, run_configs)
    SocketProtocol.start_server(connection_profile)
