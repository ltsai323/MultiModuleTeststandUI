from dataclasses import dataclass
#from SingleConnector import SingleConnector, ConnectionConfig
import SingleConnector
from tools.LogTool import LOG

import tools.SocketProtocol_ as SocketProtocol
import tools.MesgHub as MesgHub
import time


class CMD:
    CONNECT = 'connect'
    DESTROY = 'DESTROY'
    UPDATE_CONFIG = 'UPDATE'

    TAKE_DATA = 'run'
    TEST = 'test'



@dataclass
class Configurations:
    name:str

def main_func(theCONFIGs:SocketProtocol.RunningConfigurations,command:MesgHub.CMDUnit):
    theCONFIGs.MESG('CMD Received', str(command))

    def send_ssh_mesg(bashCMD:str):
        if not hasattr(theCONFIGs.connMgr,'connection'): # connection = paramiko.SSHClient()
            theCONFIGs.MESG('NotInitializedError', f'SingleConnector was not connected to any SSH server. Initialize before send any message')
            return 'nothing send to HW'
        return SingleConnector.SendCMDWithoutWaiting(theCONFIGs.connMgr,bashCMD)

    job_finished = True
    mesg_box = ''
    if command.cmd == CMD.CONNECT:
        theCONFIGs.name = command.arg # Set PyModule name
        theCONFIGs.MESG('MESG', f'current config name is {theCONFIGs.name}')
        theCONFIGs.connMgr.Initialize()
        mesg_box = f'SSH Connection Initialized.'
    if command.cmd == CMD.TAKE_DATA: # need to load command inside yaml
        out_mesg = send_ssh_mesg(f'sh runGUI.sh {theCONFIGs.boardtype} {theCONFIGs.boardID} {theCONFIGs.hexacontrollerIP} ')
        job_finished = False
    if command.cmd == CMD.TEST: # need to load command inside yaml
        out_mesg = send_ssh_mesg(f'ls&& sleep 5 && echo hiiii && sleep 5 && ls -ltr')
        job_finished = False

    if command.cmd == CMD.UPDATE_CONFIG:
        'aaa:3.14|bbb:6.28|ccc:7.19'
        theCONFIGs.SetValues(command.arg)
        mesg_box = f'Update configuration {command.arg}'

    if command.cmd == CMD.DESTROY:
        theCONFIGs.connMgr.Close()
        mesg_box = f'Closed SSH connection'


    if job_finished:
        theCONFIGs.MESG('JOB_FINISHED', mesg_box) # Notify the execution is finished.

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
    host = "192.168.50.140"
    port = 22  # Default SSH port
    user = "ntucms"
    password = "9ol.1qaz5tgb"
    default_configs = SingleConnector.ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password,
            tag = 'tobedeleted asdf',
            ) ## need to load yaml file

    # new
    def log(theSTAT:str,theMESG:str):
        LOG(theSTAT, '------------ TESTING -------------', theMESG)
    def err(theSTAT:str,theMESG:str):
        LOG(theSTAT, '------------ _ERROR_ -------------', theMESG)

    LOG('Service Activated', 'SSHConnection',f'Activate Socket@0.0.0.0:2000')
    LOG('Service Activated', 'SSHConnection',f'Connecting to {default_configs.host}:{default_configs.port} via SSH')
    run_configs = SocketProtocol.RunningConfigurations(log)
    run_configs.SetDefault(default_configs)
    run_configs.MESG = log
    setattr(run_configs, 'connMgr', SingleConnector.SingleConnector(log,err) )
    run_configs.connMgr.SetConfig(default_configs)

    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='connect')
    main_func(run_configs, socketCMD)
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='test')
    main_func(run_configs, socketCMD)
    import time
    time.sleep(5)
    socketCMD = MesgHub.CMDUnitFactory( name='testing', cmd='DESTROY')
    main_func(run_configs, socketCMD)

    print('TestFunc() Finished')
    exit()

if __name__ == "__main__":
    #TestFunc()
    # control PC
    host = "192.168.50.140"
    port = 22  # Default SSH port
    user = "ntucms"
    password = "9ol.1qaz5tgb"
    conf_cmdPCA = SingleConnector.ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password,
            tag = 'tobedeleted asdf',
            )
    default_configs = conf_cmdPCA




    # new
    LOG('Service Activated', 'SSHConnection',f'Activate Socket@0.0.0.0:2000')
    LOG('Service Activated', 'SSHConnection',f'Connecting to {default_configs.host}:{default_configs.port} via SSH')
    run_configs = SocketProtocol.RunningConfigurations()
    run_configs.SetDefault(default_configs)
    setattr(run_configs, 'connMgr', SingleConnector.SingleConnector() )
    run_configs.connMgr.SetConfig(conf_cmdPCA)

    connection_profile = SocketProtocol.SocketProfile(communicate_with_socket, run_configs)
    SocketProtocol.start_server(connection_profile, thePORT=2001)
