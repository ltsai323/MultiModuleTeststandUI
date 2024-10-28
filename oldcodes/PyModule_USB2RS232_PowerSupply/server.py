import pyvisa
import codecs
from dataclasses import dataclass
import tools.SocketProtocol_ as SocketProtocol
import tools.MesgHub as MesgHub
import time
LOG_LEVEL = 1
def BUG(*mesg):
    if LOG_LEVEL < 1:
        print('#DEBUG# ', mesg)

@dataclass
class LoadedConfigurations:
    MaximumOutputVoltage:float
    MaximumOutputCurrent:float
    ControlMode: str
    resource:str




import sys
def LOG(info,name,mesg):
    if LOG_LEVEL < 2:
        print(f'[{info} - LOG] ({name}) {mesg}', file=sys.stderr)

class CMD:
    CONNECT = 'connect'
    DESTROY = 'DESTROY'
    UPDATE_CONFIG = 'UPDATE'

    ACTIVATE_POWER_SUPPLY = 'on'
    DEACTIVATE_POWER_SUPPLY = 'off'
    SET_CONFIGS = 'set'

def GetStatus(theCONF):
    blah = ''

def main_func(theCONFIGs:SocketProtocol.RunningConfigurations,command:MesgHub.CMDUnit):
    theCONFIGs.logFUNC('CMD Received', str(command))

    def send_rs232_mesg(mesg:str):
        if not hasattr(theCONFIGs,'rm'): # rm = pyvisa.ResourceManager()
            theCONFIGs.logFUNC('NotInitializedError', f'pyvisa is not connected to RS232 device. Initialize before send any message')
        try:
            rs232_instance = theCONFIGs.rm.open_resource(theCONFIGs.resource)
            if mesg:
                rs232_instance.write(mesg)
                return 'out mesg from rs232'
        except pyvisa.VisaIOError as e:
            theCONFIGs.logFUNC('HWConnectError', f'pyvisa reports error : {type(e)} - {e}')
        finally:
            rs232_instance.close()
        return 'nothing send to HW'

    mesg_box = ''
    if command.cmd == CMD.CONNECT:
        theCONFIGs.name = command.arg # Set PyModule name
        BUG('current config name is ', theCONFIGs.name)
        theCONFIGs.rm = pyvisa.ResourceManager()
        out_mesg = send_rs232_mesg('')
        mesg_box = f'RS232 Connection checked. out_mesg = {out_mesg}'
    if command.cmd == CMD.ACTIVATE_POWER_SUPPLY:
        out_mesg = send_rs232_mesg(':OUTPUT1:STATE ON')
        mesg_box = f'Power supply activated. Voltage "{out_mesg}" and Current "{out_mesg}"'
    if command.cmd == CMD.DEACTIVATE_POWER_SUPPLY:
        out_mesg = send_rs232_mesg('OUTPUT:STATE OFF')
        mesg_box = f'Power supply disabled.'
    if command.cmd == CMD.SET_CONFIGS:
        out_mesg = send_rs232_mesg(f'VSET1:{theCONFIGs.MaximumOutputVoltage}')
        out_mesg = send_rs232_mesg(f'ISET1:{theCONFIGs.MaximumOutputCurrent}')
        out_mesg = send_rs232_mesg(f'LOAD1:{theCONFIGs.ControlMode}')
        mesg_box = f'Configs synchronized via RS232'

    if command.cmd == CMD.UPDATE_CONFIG:
        'aaa:3.14|bbb:6.28|ccc:7.19'
        theCONFIGs.SetValues(command.arg)
        mesg_box = f'Update configuration command.arg'

    if command.cmd == CMD.DESTROY:
        theCONFIGs.rm.close()
        mesg_box = f'Remove RS232 connection instance.'


    theCONFIGs.logFUNC('JOB_FINISHED', mesg_box)

def communicate_with_socket(socketPROFILE:SocketProtocol.SocketProfile, clientSOCKET,command:MesgHub.CMDUnit):
    socketPROFILE.job_is_running.set()

    def log(theSTAT,theMESG):
        LOG(theSTAT, 'execute_command', theMESG)
        SocketProtocol.UpdateMesgAndSend( socketPROFILE, clientSOCKET, theSTAT, theMESG)

    configs = socketPROFILE.configs
    configs.logFUNC = log

    main_func(configs, command)
    socketPROFILE.job_is_running.clear()

def TestFunc():
    from tools.YamlHandler import YamlLoader

    yaml_hardware = YamlLoader('config/hardware.defaults.yaml')
    yaml_hardware.LoadNewFile('config/hardware.yaml')
    LOG('config loaded', 'main', 'yaml files loaded')

    for arg_config in sys.argv[1:]:
        config_is_used = yaml_hardware.AdditionalUpdate(arg_config,keyCONFIRMATION=True)

    default_configs = LoadedConfigurations(
            resource = yaml_hardware.configs['resource'],
            MaximumOutputVoltage = yaml_hardware.configs['MaximumOutputVoltage'],
            MaximumOutputCurrent = yaml_hardware.configs['MaximumOutputCurrent'],
            ControlMode          = yaml_hardware.configs['ControlMode'],
            )
    run_configs = SocketProtocol.RunningConfigurations()
    run_configs.SetDefault(default_configs)
    run_configs.MaximumOutputVoltage = 1.5
    run_configs.MaximumOutputCurrent = 1.5
    run_configs.ControlMode = 'CV'


    def log(theSTAT,theMESG):
        LOG(theSTAT, 'execute_command', theMESG)
    run_configs.logFUNC = log
    ### main func
    cmd = MesgHub.CMDUnitFactory(name='mainController', cmd='connect', arg='myTestingFunc')
    main_func(run_configs,cmd)
    cmd = MesgHub.CMDUnitFactory(name='mainController', cmd=CMD.UPDATE_CONFIG, arg='MaximumOutputVoltage:1.5|MaximumOutputCurrent:0.2')
    main_func(run_configs,cmd)
    cmd = MesgHub.CMDUnitFactory(name='mainController', cmd=CMD.SET_CONFIGS)
    main_func(run_configs,cmd)
    cmd = MesgHub.CMDUnitFactory(name='mainController', cmd='on')
    main_func(run_configs,cmd)
    time.sleep(2)
    cmd = MesgHub.CMDUnitFactory(name='mainController', cmd='off')
    main_func(run_configs,cmd)

    print('TestFunc() Finished')
    exit(1)

if __name__ == "__main__":
    #TestFunc()
    from tools.YamlHandler import YamlLoader

    yaml_hardware = YamlLoader('config/hardware.defaults.yaml')


    # either input a .yaml file or updateSTR like resource:ASRL/dev/ttyUSB1::INSTR (Only use the first : as the separator
    for arg_config in sys.argv[1:]:
        if '.yaml' in arg_config:
            yaml_hardware.LoadNewFile(arg_config)
        else:
            config_is_used = yaml_hardware.AdditionalUpdate(arg_config,keyCONFIRMATION=True)

    default_configs = LoadedConfigurations(
            resource = yaml_hardware.configs['resource'],
            MaximumOutputVoltage = yaml_hardware.configs['MaximumOutputVoltage'],
            MaximumOutputCurrent = yaml_hardware.configs['MaximumOutputCurrent'],
            ControlMode          = yaml_hardware.configs['ControlMode'],
            )

    print('rs232 config uses recource ', default_configs.resource)
    run_configs = SocketProtocol.RunningConfigurations()
    run_configs.SetDefault(default_configs)

    connection_profile = SocketProtocol.SocketProfile(communicate_with_socket, run_configs)
    SocketProtocol.start_server(connection_profile)
