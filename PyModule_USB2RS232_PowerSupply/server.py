import pyvisa
import codecs
from dataclasses import dataclass
from tools.MesgHub import MesgEncoder
INDICATOR = 'PowerSupply'
def MESG(mesg): return MesgEncoder(INDICATOR,mesg)

@dataclass
class Configurations:
    name:str
    output_voltage:float
    resource:str


import sys
def LOG(info,name,mesg):
    print(f'[{info} - LOG] ({name}) {mesg}', file=sys.stderr)

# Create a PyVISA resource manager
def COMMAND_POOL(theCONF,cmdIDX:str ) -> tuple:
    if cmdIDX=='0': return ('OUTPUT:STATE OFF', MESG('Disabled'))
    if cmdIDX=='1': return ('OUTPUT:STATE ON' , MESG('Enabled'))
    if cmdIDX=='2': return (f'VOLTAGE {theCONF.output_voltage}', MESG(f'Power supply turned on and voltage {theCONF.output_voltage} set.'))

    raise ValueError(f'undefined input index "{cmdIDX}"')

def SendCMD(theCONF, socketINPUT:str, nothing=''):
    cmd, mesg = COMMAND_POOL(theCONF, socketINPUT)

    rm = pyvisa.ResourceManager()
    try:
        # Open the connection to the power supply
        power_supply = rm.open_resource(theCONF.resource)


        power_supply.write(cmd)
        LOG('CMD', theCONF.name,mesg)

        # Close the connection
        power_supply.close()

    except pyvisa.VisaIOError as e:
        LOG('pyvisa Error', theCONF.name,e)
        mesg = 'pyvisa ERROR ' + e
    finally:
        rm.close()

    LOG('content', 'SendCMD', mesg)
    return mesg


if __name__ == "__main__":
    from tools.YamlHandler import YamlLoader

    yaml_hardware = YamlLoader('config/hardware.defaults.yaml')
    yaml_hardware.LoadNewFile('config/hardware.yaml')
    LOG('config loaded', 'main', 'yaml files loaded')

    the_config = Configurations(name='PowerSupply',
            resource = yaml_hardware.configs['resource'],
            output_voltage = yaml_hardware.configs['output_voltage'],
            )

    from tools.SocketProtocol import SocketProtocol
    connections = SocketProtocol(the_config, SendCMD)

    LOG('Service Activated', the_config.name,f'Activate Socket@{the_config.ip}:{the_config.port}')
    connections.MultithreadListening()
