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
    yaml_hardware.AdditionalUpdate('resource:hiiii')
    yaml_hardware.AdditionalUpdate('recource:hiiii')

    the_config = Configurations(name='PowerSupply',

            resource = yaml_hardware.configs['resource'],
            output_voltage = yaml_hardware.configs['output_voltage'],
            )

    from tools.SocketProtocol import SocketProtocol
    connections = SocketProtocol(the_config, SendCMD)

    connections.MultithreadListening()
