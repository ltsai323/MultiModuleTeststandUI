#!/usr/bin/env python3
import tools.StatusDefinition as STAT_DEF
import tools.SocketCommands as SOC_CMD
from typing import Callable
import yaml

''' CMD pool : All of commands sends to PyModule '''
''' SetConfig() : The additional configs send to PyModule (Dependent to PyModule) '''
class PyModuleConnectionConfig:
    def __init__(self, name, theADDR, thePORT):
        self.name = name
        self.addr = theADDR
        self.port = thePORT

class PyModuleCommandPool:
    def __init__(self, yamlCONFIG):
        self.yaml_config = yamlCONFIG
        with open(yamlCONFIG, 'r') as ifile:
            configs = yaml.safe_load(ifile)
            self.commands = configs['available_commands']
            self.sys_cmds = configs['system_cmds']
            self.args = configs['default_args']
            '''
            systemCMD = 'CONNECT'
            systemCMD = 'RUN'
            systemCMD = 'STOP'
            for serialCMD in self.sys_cmds[systemCMD]:
                if '_PASS_' == serialCMD['cmd']: continue
                sendall(serialCMD['cmd'])
                if 'timegap' in serialCMD:
                    time.sleep(serialCMD['timegap'])
            systemCMD = 'CONFIGURE'
            update_list = []
            for serialCMD in self.syst_cmds[systemCMD]:
                c = serialCMD['cmd']
                if '_PASS_' == serialCMD['cmd']: continue
                update_list.append( MesgHub.CMDUnitFactory('update', f'{c}:{self.args[c]}') )
            sendall( SendMultipleMesg(*update_list)
            '''

            self.check_system_commands()
    def check_system_commands(self):
        for sys_cmd, detail_cmd_list in self.sys_cmds.items():
            for detail_cmd in detail_cmd_list:
                cmd = detail_cmd['cmd']
                if cmd == '_PASS_':
                    continue

                if sys_cmd == "CONFIGURE":
                    for arg in detail_cmd['configs']:
                        if arg not in [ reg_arg for reg_arg in self.args.keys() ]:
                            raise ImportError(f'configuring arg "{arg}" of system command "{sys_cmd}" not registed in default_args in {self.yaml_config}')
                else:
                    if cmd not in [ reg_cmd['cmd'] for reg_cmd in self.commands ]:
                        raise ImportError(f'running cmd "{cmd}" of system command "{sys_cmd}" not registed in available_commands in {self.yaml_config}')






class SubUnit:
    def __init__(self, cmdCONFIG:PyModuleConnectionConfig, cmdPOOL:PyModuleCommandPool):
        self.connect_config = cmdCONFIG
        self.status, self.message = STAT_DEF.N_A
        self.cmd_pool = cmdPOOL
    @property
    def CommandList(self):
        return [ cmd['cmd'] for cmd in self.cmd_pool.commands ]
    @property
    def ConfigDict(self):
        return self.cmd_pool.args
    @property
    def name(self):
        return self.connect_config.name

    def AllConfigsAsUpdateArg(self):
        return '|'.join( [f'{key}:{val}' for key,val in self.ConfigDict.items()] )
    def ConfigsAsUpdateArg(self, *confKEYs):
        return '|'.join( [f'{key}:{self.ConfigDict[key]}' for key in confKEYs] )

    def SetConfig(self, name,val):
        if name in self.cmd_pool.args: self.cmd_pool.args[name] = val
        else: raise KeyError(f'SetConfig(): config "{name}" does not exist in {self.cmd_pool.yaml_config}!')


    def Help(self):
        print('-'*20)
        print(f'Available commands for {self.name}')
        for cmd in self.cmd_pool.commands:
            print(f'CMD "{cmd}"')
        print('-'*20)

if __name__ == "__main__":
    pwrconn = PyModuleConnectionConfig('PWR1', '192.168.50.60', 2000)
    pwrconf = PyModuleCommandPool('data/subunit_testsample.yaml')
    pwrunit = SubUnit(pwrconn,pwrconf)

    print(pwrunit.cmd_pool.GetConfig('volt'))
    pwrunit.Help()
    print(pwrunit.CommandList)
