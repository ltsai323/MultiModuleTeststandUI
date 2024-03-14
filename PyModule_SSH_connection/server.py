from dataclasses import dataclass
from SingleConnector import SingleConnector, ConnectionConfig
from tools.LogTool import LOG

conn_hexCtrl = SingleConnector()
conn_cmdPC0 = SingleConnector()
conn_cmdPC1 = SingleConnector()

class CMD:
    CONNECT = 'connect'
    DESTROY = 'DESTROY'
    UPDATE_CONFIG = 'UPDATE'

    LONG_CONNECTION = 'on'
    DEACTIVATE_POWER_SUPPLY = 'off'
    SET_CONFIGS = 'set'

# Create a PyVISA resource manager
def COMMAND_POOL(theCONF,cmdIDX:str ) -> tuple:
    LOG('Receive CMD', 'COMMAND_POOL', f'Command "{cmdIDX}" received')

    if cmdIDX=='hI': return (None, conn_hexCtrl.Init())
    if cmdIDX=='hC': return (None, conn_hexCtrl.Close())
    if cmdIDX=='h0': return (None, conn_hexCtrl.SendCMD('cd ~/hgcal_daq && ./turnOff.sh'))
    if cmdIDX=='h1': return (None, conn_hexCtrl.SendCMD('cd ~/hgcal_daq && ./turnOn_FW_V3.sh'))

    if cmdIDX=='AI': return (None, conn_cmdPC0.Init())
    if cmdIDX=='AC': return (None, conn_cmdPC0.Close())
    if cmdIDX=='A1': return (None, conn_cmdPC0.SendCMD('daq-client'))

    if cmdIDX=='BI': return (None, conn_cmdPC1.Init())
    if cmdIDX=='BC': return (None, conn_cmdPC1.Close())
    if cmdIDX=='B1': return (None, conn_cmdPC1.SendCMD('cd ~/V3HD_hexactrl && ./run.sh new_testing_from_GUI'))

    if cmdIDX=='TT': return (None, conn_cmdPC1.SendCMD('ls'))


    raise ValueError(f'undefined input index "{cmdIDX}"')

def SendCMD(theCONF, socketINPUT:str, nothing=''):
    LOG('blah', 'SendCMD', 'blah blah blah')
    cmd, mesg = COMMAND_POOL(theCONF, socketINPUT)

    LOG('content', 'SendCMD', mesg)
    return mesg


@dataclass
class Configurations:
    name:str
def TestFunc():
    # control PC
    host = "192.168.50.140"
    port = 22  # Default SSH port
    user = "ntucms"
    password = "9ol.1qaz5tgb"
    conf_cmdPCA = ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password,
            tag = 'CommandPCA',
            )
    print('End of test func.')

    exit(1)
if __name__ == "__main__":
    # control PC
    host = "192.168.50.140"
    port = 22  # Default SSH port
    user = "ntucms"
    password = "9ol.1qaz5tgb"
    conf_cmdPCA = ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password,
            tag = 'CommandPCA',
            )
    conn_cmdPC0.SetConfig(conf_cmdPCA)
    conf_cmdPCB = ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password,
            tag = 'CommandPCB',
            )
    conn_cmdPC1.SetConfig(conf_cmdPCB)


    # hexa controler
    host = "192.168.50.152"
    port = 22  # Default SSH port
    user = "root"
    password = "centos"
    conf_hexCtrl = ConnectionConfig(
            host = host,
            port = port,
            user = user,
            pwd = password,
            tag = 'HexaController',
            )
    conn_hexCtrl.SetConfig(conf_hexCtrl)


    the_config = Configurations(
            name= 'SSHConnection',
            )

    TestFunc()

    from tools.SocketProtocol import SocketProtocol
    connections = SocketProtocol(the_config, SendCMD)
    LOG('Service Activated', the_config.name,f'Activate Socket@0.0.0.0:2000')
    #connections.MultithreadListening()
    connections.SingleThreadListening()
