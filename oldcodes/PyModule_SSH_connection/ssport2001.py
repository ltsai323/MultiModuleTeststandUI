from dataclasses import dataclass
#from SingleConnector import SingleConnector, ConnectionConfig
import SingleConnector
from tools.LogTool import LOG

import tools.SocketProtocol_ as SocketProtocol
import tools.MesgHub as MesgHub
import time
import re



class CMDConnect:
    remote_cmd = 'connect'
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> str:
        theCONFIGs.name = self.cmd_unit.name
        theCONFIGs.MESG('NameUpdated', f'PyModule name is set from remote "{theCONFIGs.name}"')
        theCONFIGs.connMgr.Initialize()
        return False # no waiting for job ended
class CMDDestroy:
    remote_cmd = 'DESTROY'
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        time.sleep(1.0)
        remote_cmd_set = theCONFIGs.destroyCMD
        out_mesg = send_ssh_mesg(theCONFIGs, full_CMD_with_args(theCONFIGs,remote_cmd_set['cmd']) )
        time.sleep( remote_cmd_set['delay'] )
        theCONFIGs.connMgr.Close() # no matter the command executed or not. Destroy the connection instance in python.
        if remote_cmd_set['type'] == 'waiting_for_job_ended':
            return True # waiting for job ended
        return False
class CMDRun:
    remote_cmd = 'run'
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        remote_cmd_set = theCONFIGs.runCMD
        out_mesg = send_ssh_mesg(theCONFIGs, full_CMD_with_args(theCONFIGs,remote_cmd_set['cmd']) )
        time.sleep( remote_cmd_set['delay'] )
        if remote_cmd_set['type'] == 'waiting_for_job_ended':
            return True # waiting for job ended
        return False
class CMDTest:
    remote_cmd = 'test'
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        remote_cmd_set = theCONFIGs.testCMD
        out_mesg = send_ssh_mesg(theCONFIGs, full_CMD_with_args(theCONFIGs,remote_cmd_set['cmd']) )
        time.sleep( remote_cmd_set['delay'] )
        if remote_cmd_set['type'] == 'waiting_for_job_ended':
            return True # waiting for job ended
        return False


class CMDConfigure:
    remote_cmd = 'UPDATE'
    def __init__(self, cmdUNIT:MesgHub.CMDUnit):
        self.cmd_unit = cmdUNIT
    def execute(self,theCONFIGs:SocketProtocol.RunningConfigurations) -> bool:
        'aaa:3.14|bbb:6.28|ccc:7.19'
        theCONFIGs.SetValues(self.cmd_unit.arg)
        theCONFIGs.MESG('ConfigUpdated', f'Update configuration {self.cmd_unit.arg}')

        return False
def CMDInstanceFactory(cmdUNIT:MesgHub.CMDUnit):
    if cmdUNIT.cmd == CMDConnect.remote_cmd:
        return CMDConnect(cmdUNIT)
    if cmdUNIT.cmd == CMDDestroy.remote_cmd:
        return CMDDestroy(cmdUNIT)
    if cmdUNIT.cmd == CMDRun.remote_cmd:
        return CMDRun(cmdUNIT)
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

def send_ssh_mesg(theCONFIGs:SocketProtocol.RunningConfigurations,bashCMD:str):
    if not hasattr(theCONFIGs.connMgr,'connection'): # connection = paramiko.SSHClient()
        theCONFIGs.MESG('NotInitializedError', f'SingleConnector was not connected to any SSH server. Initialize before send any message. cmd[{bashCMD}]')
        return 'nothing send to HW'
    return SingleConnector.SendCMDWithoutWaiting(theCONFIGs.connMgr,bashCMD)

def main_func(theCONFIGs:SocketProtocol.RunningConfigurations,command:MesgHub.CMDUnit):
    theCONFIGs.MESG('CMD Received', command.cmd)


    still_running = False
    mesg_box = ''
    exec_unit = CMDInstanceFactory(command)
    if exec_unit:
        still_running = exec_unit.execute(theCONFIGs)


    if not still_running:
        theCONFIGs.MESG('JOB_FINISHED', f'running cmd {command.cmd}') # Notify the execution is finished.

def communicate_with_socket(socketPROFILE:SocketProtocol.SocketProfile, clientSOCKET,command:MesgHub.CMDUnit):
    socketPROFILE.job_is_running.set()

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
    socketPROFILE.job_is_running.clear()
def TestFunc():
    ### put yaml file asdf
    # control PC
    from tools.YamlHandler import YamlLoader
    inputFILE='config/sshconfigs.commanderPC.yaml'
    inputFILE='config/sshconfigs.hexacontroller.yaml'
    loadedCONFIGs = YamlLoader(inputFILE)

    default_configs = SingleConnector.ConnectionConfig(
            host = loadedCONFIGs.configs['host'],
            port = loadedCONFIGs.configs['port'],
            user = loadedCONFIGs.configs['user'],
            pwd = loadedCONFIGs.configs['password'],
            )

    # new
    def log(theSTAT:str,theMESG:str):
        LOG(theSTAT, '------------ TESTING -------------', theMESG)
    def err(theSTAT:str,theMESG:str):
        LOG(theSTAT, '------------ _ERROR_ -------------', theMESG)

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

    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='connect')
    main_func(run_configs, socketCMD)
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='test')
    main_func(run_configs, socketCMD)
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='run')
    main_func(run_configs, socketCMD)
    import time
    time.sleep(5)
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='DESTROY')
    print('TestFunc() middle term')
    main_func(run_configs, socketCMD)

    print('TestFunc() Finished')
    exit()

if __name__ == "__main__":
    #TestFunc()
    # control PC
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
    SocketProtocol.start_server(connection_profile, thePORT=2001)
