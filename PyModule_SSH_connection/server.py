from dataclasses import dataclass
from SingleConnector import SingleConnector, ConnectionConfig
from tools.LogTool import LOG

conn_hexCtrl = SingleConnector()
conn_cmdPC0 = SingleConnector()
conn_cmdPC1 = SingleConnector()

# Create a PyVISA resource manager
def COMMAND_POOL(theCONF,cmdIDX:str ) -> tuple:
    if cmdIDX=='hI': return (None, conn_hexCtrl.Init())
    if cmdIDX=='hC': return (None, conn_hexCtrl.Close())
    if cmdIDX=='h0': return (None, conn_hexCtrl.SendCMD('cd ~/hgcal_daq && ./turnOff.sh'))
    if cmdIDX=='h1': return (None, conn_hexCtrl.SendCMD('cd ~/hgcal_daq && ./turnOn_FW_V3.sh'))

    if cmdIDX=='AI': return (None, conn_cmdPC0.Init())
    if cmdIDX=='AC': return (None, conn_cmdPC0.Close())
    if cmdIDX=='A1': return (None, conn_cmdPC0.SendCMD('daq-client'))

    if cmdIDX=='BI': return (None, conn_cmdPC1.Init())
    if cmdIDX=='BC': return (None, conn_cmdPC1.Close())
    if cmdIDX=='B1': return (None, conn_cmdPC1.SendCMD('cd ~/V3HD_hexactrl && ./run.sh testing'))

    if cmdIDX=='TT': return (None, conn_cmdPC1.MESG('hiii tested'))


    raise ValueError(f'undefined input index "{cmdIDX}"')

def SendCMD(theCONF, socketINPUT:str, nothing=''):
    cmd, mesg = COMMAND_POOL(theCONF, socketINPUT)

    LOG('content', 'SendCMD', mesg)
    return mesg


@dataclass
class Configurations:
    name:str
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
    from tools.SocketProtocol import SocketProtocol
    connections = SocketProtocol(the_config, SendCMD)
    LOG('Service Activated', the_config.name,f'Activate Socket@0.0.0.0:2000')
    #connections.MultithreadListening()
    connections.SingleThreadListening()
