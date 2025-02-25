from abc import ABC, abstractmethod

VALID_CONFIG = '' # Nothing means it is a valid config

class JobFragBase(ABC):
    '''
    A Job Fragment defined used single function. Define the following functions:
    :__init__: Initialize this object
    :__del__:  delete this object. This is used as the "Destroy" action
    :Initialize: Different from __init__(), this function needs to check all runtime dependencies.
                 For example, check loaded file, check SSH destination.
    :Configure: Input a dictionary for update self.config
    :Run: Run function without any argument. You need to use Configure() to set all arguments.
    :Stop: Stop the running actions.
    '''

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def __del__(self):
        pass


    @abstractmethod
    def Initialize(self):
        pass

    @abstractmethod
    def Configure(self, updatedCONF:dict) -> bool:
        pass

    def set_cmd_template(self, cmdTEMPLATE:dict):
        self.cmd_template = cmdTEMPLATE
    def set_config(self, conf:dict):
        self.config = conf
    def set_config_const(self, confCONST:dict):
        self.config_const = confCONST
    def set_config_value(self, key:str, val) -> str:
        if key in self.config.keys():
            # add additional validator here
            self.config[key] = val
            return VALID_CONFIG
        return 'InvalidKey'
        
    def show_configurations(self) -> dict:
        return self.config
    def get_full_command_from_cmd_template(self, templateNAME) -> dict:
        d = self.config_const | self.config # | operation requiring python3p9
        try:
            return self.cmd_template[templateNAME].format(**d)
        except KeyError as e:
            raise KeyError(f'[CMDNotFound] Command "{ templateNAME }" is not registed in cmd_template. The available keys are "{ self.cmd_template.keys() }"') from e


        

    @abstractmethod
    def Run(self):
        pass

    @abstractmethod
    def Stop(self):
        pass

