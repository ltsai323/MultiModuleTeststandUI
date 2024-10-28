#!/usr/bin/env python3
import yaml

def LoadYAML(yamlFILE) -> dict:
    with open(yamlFILE,'r') as f:
        return yaml.safe_load(f)

class LoadParameter:
    def __init__(self, name, conf):
        self.name = name
        self.input_type = conf['inputtype']
        has_options = False
        if self.input_type == 'radio'   : has_options = True
        if self.input_type == 'checkbox': has_options = True

        if not has_options:
            self.value = conf['value']
            self.options = None
        else:
            self.value = conf['value'][0]
            self.options = conf['value']
    def __str__(self):
        return f'LoadParameter(name={self.name}, value={self.value}, options={self.options}, input_type={self.input_type})'
def LoadParameterFactory(yamlLOADEDdict:dict) -> dict:
    return { name: LoadParameter(name, content)
             for name,content in yamlLOADEDdict['loaded_parameters'].items() }

JOB_TYPES = [ 
    'normal',
    'background monitor',
    'destroy job',
    ]
class StagedCMD:
    def __init__(self, name, conf):
        self.name = name
        self.job_type = conf['job_type']
        self.bash_cmd = conf['bash_cmd'] if 'bash_cmd' in conf else None

    def __str__(self):
        return f'StagedCMD(name={self.name}, job_type={self.job_type})'
def StagedCMDFactory(yamlLOADEDdict:dict) -> dict:
    return { name: StagedCMD(name, content)
             for name,content in yamlLOADEDdict['StagedCMD'].items() }



class CMDParameter:
    def __init__(self, name, yamlFILE):
        self.name = name

        theconf = LoadYAML(yamlFILE)
        self.stagedCMDs = StagedCMDFactory(theconf)
        self.configs = LoadParameterFactory(theconf)
    def exec(self):
        raise NoImplementedError()
    def __str__(self):
        return f'{type(self).__name__}(name={self.name})'

class CMDParameterTest(CMDParameter):
    identifier = 'test'
    def __init__(self, name, yamlFILE):
        super().__init__(name,yamlFILE)
    def exec(self):
        print('hiiii')
        print(self.stagedCMDs['RUN'])

class CMDParameterSSHAccess(CMDParameter):
    identifier = 'test'
    def __init__(self,  usedCONF):
        super().__init__(usedCONF)
    def exec(self):
        print('hiiii')




def GetBashCommand(cmdUNIT, cmd:str) -> str:
    if cmd not in cmdUNIT.stagedCMDs:
        raise NotImplementedError(f'command {cmd} is not implemented in {cmdUNIT.name}')

    the_cmd_unit = cmdUNIT.stagedCMDs[cmd]
    fullcmd = the_cmd_unit.bash_cmd

    if fullcmd is None: return ''
    return fullcmd.format(**{cname:cvar.value for cname,cvar in cmdUNIT.configs.items()} )

def GetJobType(cmdUNIT, cmd:str) -> str:
    if cmd not in cmdUNIT.stagedCMDs:
        raise NotImplementedError(f'command {cmd} is not implemented in {cmdUNIT.name}')

    the_cmd_unit = cmdUNIT.stagedCMDs[cmd]
    if the_cmd_unit.job_type not in JOB_TYPES:
        raise NotImplementedError(f'job type {the_cmd_unit.job_type} not implemented in CommandUnits')
    return the_cmd_unit.job_type






if __name__ == "__main__":
    yamlfile = 'test.yaml'
    a = CMDParameterTest('test', yamlfile)
    print(a.__dir__())
    
    bash_cmd = GetBashCommand(a, 'RUN')
    jobtype = GetJobType(a, 'RUN')

    print(f'[{jobtype}] command: {bash_cmd}')
    print(type(a).__name__)
    print(a)


    #print(a.hexa_controller_address)
    #print(a.user)

    #fail = CMDParameter()
    #fail.exec()
