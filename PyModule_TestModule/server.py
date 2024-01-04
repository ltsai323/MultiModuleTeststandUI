import codecs
from dataclasses import dataclass

@dataclass
class Configurations:
    name:str

    port:int
    mesg_length:int
    ip:str

    output_voltage:float
    resource:str


import sys
def LOG(info,name,mesg):
    print(f'[{info} - LOG] ({name}) {mesg}', file=sys.stderr)


def SendCMD(theCONF, socketINPUT:str, nothing=''):
    mesg='testing module'
    LOG('mesg', 'SendCMD', mesg)

    return mesg


if __name__ == "__main__":
    from tools.YamlHandler import YamlLoader
    yaml_connections = YamlLoader('config/socket_connections.defaults.yaml')
    yaml_connections.LoadNewFile('config/socket_connections.yaml', ignoreNEWkey=True)

    yaml_hardware = YamlLoader('config/hardware.defaults.yaml')
    yaml_hardware.LoadNewFile('config/hardware.yaml')
    LOG('config loaded', 'main', 'yaml files loaded')

    the_config = Configurations(name='PowerSupply',
            port=yaml_connections.configs['port'],
            mesg_length=yaml_connections.configs['mesg_length'],
            ip=yaml_connections.configs['ip'],

            resource = yaml_hardware.configs['resource'],
            output_voltage = yaml_hardware.configs['output_voltage'],
            )

    from tools.SocketProtocol import SocketProtocol
    connections = SocketProtocol(the_config, SendCMD)

    LOG('Service Activated', the_config.name,f'Activate Socket@{the_config.ip}:{the_config.port}')
    connections.MultithreadListening()
