import codecs
from dataclasses import dataclass

@dataclass
class Configurations:
    name:str

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
    LOG('input arg', 'mainfunc', sys.argv)
    from tools.YamlHandler import YamlLoader

    yaml_hardware = YamlLoader('config/hardware.defaults.yaml')
    #yaml_hardware.LoadNewFile('config/hardware.yaml')
    yaml_hardware.LoadNewFile('config/hardware.test.yaml')
    LOG('config loaded', 'main', 'yaml files loaded')

    the_config = Configurations(name='PowerSupply',

            resource = yaml_hardware.configs['resource'],
            output_voltage = yaml_hardware.configs['output_voltage'],
            )

    from tools.SocketProtocol import SocketProtocol
    connections = SocketProtocol(the_config, SendCMD)

    LOG('Service Activated', the_config.name,f'Activate Socket@{the_config.ip}:{the_config.port}')
    connections.MultithreadListening()
