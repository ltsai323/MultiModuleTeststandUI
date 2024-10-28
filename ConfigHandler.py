#!/usr/bin/env python3

DEBUG=False

# loaded parameter will be modified while program execution
class LoadedParameterBasics:
    parType = ''
    def __init__(self, key,val):
        self.key=key
        self.val=''
    def GetCurrentValue(self):
        return self.val
    def __str__(self):
        return f'LoadParameterBasics{self.GetCurrentValue()}'
class LoadedParameterText:
    parType = 'text'
    def __init__(self, key,val):
        self.key=key
        self.val=val['value']
    def GetCurrentValue(self):
        return self.val
    def __str__(self):
        return f'LoadParameterText{self.GetCurrentValue()}'
class LoadedParameterRadio:
    parType = 'radio'
    def __init__(self, key,val):
        self.key=key
        self.val=val['value']
        self.options=val['options']
    def GetCurrentValue(self):
        if self.val != "":
            if self.val not in self.options:
                raise IOError(f"[InvalidValue] LoadedParameterTextRadio::GetCurrentValue() : current value {self.val} not in options {self.options}")
                #print(f"[IgnoreInvalidValue] LoadedParameterRadio::GetCurrentValue() : current value {self.val} not in options {self.options}")

        return self.val
    def __str__(self):
        return f'LoadParameterRadio{self.GetCurrentValue()}'
class LoadedParameterRadioField(LoadedParameterBasics):
    parType = 'radiofield'
    def __init__(self, key,val):
        super().__init__(key,val)
        self.options=val['options']
    def GetCurrentValue(self):
        if self.val != "":
            if self.val not in self.options:
                raise IOError(f"[InvalidValue] LoadedParameterTextRadio::GetCurrentValue() : current value {self.val} not in options {self.options}")
                #print(f"[IgnoreInvalidValue] LoadedParameterRadioField::GetCurrentValue() : current value {self.val} not in options {self.options}")
        return self.val
    def __str__(self):
        return f'LoadedParameterRadioField({self.GetCurrentValue()})'
class LoadedParameterIntegerField(LoadedParameterBasics):
    parType = 'integerfield'
    def __init__(self, key,val):
        super().__init__(key,val)
    def __str__(self):
        return f'LoadedParameterIntegerField({self.GetCurrentValue()})'
class LoadedParameterStringField(LoadedParameterBasics):
    parType = 'stringfield'
    def __init__(self, key,val):
        super().__init__(key,val)
    def __str__(self):
        return f'LoadedParameterStringField({self.GetCurrentValue()})'


class LoadedParameterFactory:
    def __init__(self,yamlLOADERoutput:dict):
        d = yamlLOADERoutput.configs['parameters']
        self.parameters = []
        if not d: return
        type_and_constructors = {
                LoadedParameterText        .parType: LoadedParameterText,
                LoadedParameterRadio       .parType: LoadedParameterRadio,
                LoadedParameterRadioField  .parType: LoadedParameterRadioField,
                LoadedParameterStringField .parType: LoadedParameterStringField,
                LoadedParameterIntegerField.parType: LoadedParameterIntegerField,
                }
        for name, conf in d.items():
            if conf['type'] in type_and_constructors.keys():
                loaded_parameter = type_and_constructors[ conf['type'] ]
                self.parameters.append(loaded_parameter(name,conf))
            else:
                mesg=f'[YamlConfigError] config "{conf["type"]}" from yaml file does not match any of LadedParameterSOMEField defined in ConfigHandler.py'
                raise KeyError(mesg)

        '''
        for name, conf in d.items():
            loaded_parameter = LoadedParameterText
            if conf['type'] == loaded_parameter.parType:
                self.parameters.append(loaded_parameter(name,conf))
            loaded_parameter = LoadedParameterRadio
            if conf['type'] == loaded_parameter.parType:
                self.parameters.append(loaded_parameter(name,conf))
            loaded_parameter = LoadedParameterRadioField
            if conf['type'] == loaded_parameter.parType:
                self.parameters.append(loaded_parameter(name,conf))
            loaded_parameter = LoadedParameterStringField
            if conf['type'] == loaded_parameter.parType:
                self.parameters.append(loaded_parameter(name,conf))
            loaded_parameter = LoadedParameterIntegerField
            if conf['type'] == loaded_parameter.parType:
                self.parameters.append(loaded_parameter(name,conf))
        '''
    def SetPar(self,key,val):
        if key not in (p.key for p in self.parameters):
            raise KeyError(f'[FailedSetParameter] SetPar() : key "{key}" not found in parameters.')
            #print(f'[IgnoreInvalidKey] SetPar() : key "{key}" not found in parameters.')
        for par in self.parameters:
            if par.key == key:
                par.val = val
    def GetParDict(self) -> dict:
        return { loadedPAR.key:loadedPAR.GetCurrentValue() for loadedPAR in self.parameters }


# LoadedConfig is the configuration to the program, this value will not be modified while job execution
def LoadedConfigFactory(yamlLOADERoutput:dict) -> dict:
    d = yamlLOADERoutput.configs['configs']
    if d == None: return {}
    return { var:val for var,val in d.items() }

class LoadedCMDFactory:
    def __init__(self, yamlLOADERoutput:dict):
        d = yamlLOADERoutput.configs['stagedCMD']
        class CMDConfig:
            def __init__(self,conf):
                self.cmd = conf['cmd']
                #self.type = getattr(conf,'type', 'None')
                self.delay = conf['delay']

        self.command_set = { cmd:CMDConfig(conf) for cmd, conf in d.items() }
    def GetCMD(self, stagedCMD:str, parDICT:dict):
        if stagedCMD not in self.command_set:
            raise KeyError(f'[StagedCMDNotFound] StagedCMD "{stagedCMD}" cannot be found in the command_set')
        return self.command_set[stagedCMD].cmd.format(**parDICT)
    def __str__(self):
        return f'LoadedCMDFactory contains staged CMD : {self.command_set.keys()}'
