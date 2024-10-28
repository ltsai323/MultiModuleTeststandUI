#!/usr/bin/env python3
import logging

class STATUS_CODE:
    initialized = -1
    error = -9

    idle = 0
    busy = 1

__default_log_statuscode = {
        'MesgError': 0,
        'MesgOut': 1,
        }

def __default_log(stat,mesg):
    logging.info(f'[{stat}] {mesg}')
    stat = 'MesgOut'
    logging.debug(f'[{__default_log_statuscode[stat]}] {mesg}')

# the configurations would be further implemented while running
class RunningConfigurations:
    def __init__(self, logMETHOD):
        self.status = STATUS_CODE.initialized
        self.name = 'NotInitialized'
        self.logFUNC = logMETHOD
        self.configs = {}

    def LOG(self, stat, mesg):
        self.logFUNC(stat,mesg)

    def SetValues(self, confDICT:dict):
        # no checker here. Put everything needed here
        self.configs.update(confDICT)
    def Get(self,key):
        if key in self.configs: return self.configs[key]
        self.LOG(f'[ConfKeyNotFound] key "{key}" is invalid in running configuration')
        raise KeyError(f'[ConfKeyNotFound] key "{key}" is invalid in running configuration')

if __name__ == "__MAIN__".lower():
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',level=logging.DEBUG)
    runconf = RunningConfigurations(__default_log)
    runconf.LOG('mesg out', 'tttttttttt')

    fake_conf = {
            'par1': 1,
            'par2': { 'par21': 21, 'par22': 22 },
            'par3': 3,
            }

    runconf.SetValues(fake_conf)
    print(runconf.Get('par1'))

