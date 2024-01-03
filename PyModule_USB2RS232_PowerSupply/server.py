import pyvisa
import codecs
from dataclasses import dataclass

@dataclass
class Configurations:
    name:str

    port:int
    mesg_length:int
    ip:str
    resource:str

    output_voltage:float


def LOG(info,name,mesg):
    print(f'[{info} - LOG] ({name}) {mesg}')

# Create a PyVISA resource manager
def COMMAND_POOL(theCONF,cmdIDX:str ) -> tuple:
    if cmdIDX=='0': return ('OUTPUT:STATE OFF', 'Disable the output')
    if cmdIDX=='1': return ('OUTPUT:STATE ON' ,  'Enable the output')
    if cmdIDX=='2': return (f'VOLTAGE {theCONF.output_voltage}', f'Power supply turned on and voltage {theCONF.output_voltage} set.')

    raise ValueError(f'undefined input index "{cmdIDX}"')

def SendCMD(theCONF, socketINPUT:str, nothing=''):
    cmd, mesg = COMMAND_POOL(theCONF, socketINPUT)

    rm = pyvisa.ResourceManager()
    mesg=''
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

    return mesg


if __name__ == "__main__":
    from tools.YamlHandler import YamlLoader
    yaml_connections = YamlLoader('config/connections.defaults.yaml')
    yaml_connections.LoadNewFile('config/connections.yaml', ignoreNEWkey=True)

    yaml_hardware = YamlLoader('config/hardware.defaults.yaml')
    yaml_hardware.LoadNewFile('config/hardware.yaml')

    the_config = Configurations(name='PowerSupply',
            port=yaml_connections.configs['port'],
            mesg_length=yaml_connections.configs['mesg_length'],
            ip=yaml_connections.configs['ip'],
            resource = yaml_connections.configs['resource'],

            output_voltage = yaml_hardware.configs['output_voltage'],
            )

    from tools.SocketProtocol import SocketProtocol
    connections = SocketProtocol(the_config, SendCMD)

    LOG('Service Activated', the_config.name,f'Activate Socket@{the_config.ip}:{the_config.port}')
    connections.MultithreadListening()