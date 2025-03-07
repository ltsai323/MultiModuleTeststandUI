import asyncio
import weakref
import logging
from abc import ABC, abstractmethod

class AsyncManager(ABC):
    def __init__(self, stdOUT,stdERR , cmdTEMPLATEs:dict, argCONFIGs:dict, constargCONFIGs:dict):
        weakref.finalize(self, self._cleanup) # add a weak reference to __del__()

        self.set_logger(stdOUT,stdERR)

        self.set_cmd_template(cmdTEMPLATEs)
        self.set_config(argCONFIGs)
        self.set_config_const(constargCONFIGs)


    ### env setup ON
    @abstractmethod
    async def Initialize(self):
        raise NotImplementedError('Initialize() requires to be implemented.')

    ### env setup OFF
    #@abstractmethod
    #async def Destroy(self):
    #    raise NotImplementedError('Destroy() requires to be implemented.')
    @abstractmethod
    def Destroy(self):
        raise NotImplementedError('Destroy() requires to be implemented.')

    
    ### run stage ON
    @abstractmethod
    async def Run(self):
        raise NotImplementedError('Run() requires to be implemented.')


    ### run stage ON
    @abstractmethod
    async def Stop(self):
        raise NotImplementedError('Stop() requires to be implemented.')



    def _cleanup(self):
        """Cleans up when instance is deleted."""
        self.Destroy()
        return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.Destroy())
            else:
                loop.run_until_complete(self.Destroy())
        except RuntimeError:
            self.log.info('[NoEventLoop] So __del__() skips executing self.Destroy().')
            return # once event loop no more exist. Not to execute
            #asyncio.run( self.Destroy() )


    ### Do Destroy before delete instance
    def __del__(self):
        """Ensures cleanup when instance is deleted."""
        self.log.debug('__del__() exec')
        try:
            self._cleanup()
        except Exception:
            pass  # Avoid any errors during deletion
        self.log.debug('__del__() exec ENDED')

    def set_cmd_template(self, cmdTEMPLATE:dict):
        self.cmd_template = cmdTEMPLATE
    def set_config(self, conf:dict):
        self.config = conf
    def set_config_const(self, confCONST:dict):
        self.config_const = confCONST

    def set_value_to_config(self, key:str, val) -> str:
        if key in self.config.keys():
            # add additional validator here
            self.config[key] = val
            return VALID_CONFIG
        return ERRORCODE_INVALID_CONFIG


    def get_full_command_from_cmd_template(self, templateNAME) -> dict:
        d = self.config_const | self.config # | operation requiring python3p9
        try:
            return self.cmd_template[templateNAME].format(**d)
        except KeyError as e:
            raise KeyError(f'[CMDNotFound] Command "{ templateNAME }" is not registed in cmd_template. The available keys are "{ self.cmd_template.keys() }"') from e
        except IndexError as e:
            raise IndexError(f'\n\n[InvalidCMD] the command "{ self.cmd_template[templateNAME] }" might be incorrected under python format() function. Please modify it. Especially for bracket {{ and }} is a reserved character\n\n') from e

    def set_logger(self, stdOUT, stdERR):
        self.log = stdOUT
        self.err = stdERR


    def Configure(self, updatedCONF:dict) -> bool:
        '''
        Update old argument config only if all configs in old argument config being confirmed.
        If there are some redundant key - value pair in updatedCONF, these configs are ignored.

        updatedCONF: dict. It should have the same format with original arg config
        '''
        for key, value in updatedCONF.items():
            error_mesg = self.set_value_to_config(key,value)
            if error_mesg:
                self.err.warning(f'[{error_mesg}] Invalid configuration from config: key "{ key }" and value "{ value }".')
                return False
        return True
    def show_configurations(self) -> dict:
        return self.config
    def show_all_configurations(self):
        self.log.info(f'[Configs] variant = {self.config} and Constant = {self.config_const}')
