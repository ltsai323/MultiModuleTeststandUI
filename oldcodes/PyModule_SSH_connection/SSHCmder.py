#!/usr/bin/env python3
class ParameterPool:
    def __init__(self, theDICT:dict):
        self.load_dict = theDICT
    def get_par(self):
        return self.load_dict
def ParameterPoolFactory(loadDICT):
    return ParameterPoolFactory(loadDICT['Parameters'])

JOB_TYPE = {
   'waiting': 'waiting_for_job_ended',
   'monitor': 'monitoring',
   'default': 'waiting_fot_job_ended',
   }



class CMDDetail:
    def __init__(self, stageNAME:str,loadDICT:dict):
        self.stage_name = stageNAME
        self.cmd = loadDICT['cmd']
        self.job_type = loadDICT['type'] if loadDICT['type'] in JOB_TYPE.values() else JOB_TYPE['default']
        self.job_finished_delay = loadDICT['delay']

import tools.MesgHub as MesgHub
def LOG(mesgUNIT:MesgHub.MesgUnit):
    print(f'[{mesgUNIT.stat}] {mesgUNIT.name} -- {mesgUNIT.mesg} ({mesgUNIT.timestamp})')
import paramiko
import threading
class PyModule_SSHCmder_general:
    def __init__(self, logMETHOD, cmdDETAILdict:dict):
        self.LOG = logMETHOD
        self.cmd_details = { name:CMDDetail(name,cmd_content) for name,cmd_content in cmdDETAILdict.items() }
def PyModule_SSHCmder_Factory(loadDICT:dict):
    par_pool = ParameterPoolFactory(loadDICT)
    if loadDICT['Module'] == 'SSHCmder':
        return PyModule_SSHCmder_general(loadDICT['CMDDetails'], par_pool)

class PyModule_SSHCmder_Checker:
    def __init__(self, generalCMDER:PyModule_SSHCmder_general):
        self.general = generalCMDER

    def execute(self, parPOOL:ParameterPool):
        conn = None
        try:
            conn = paramiko.SSHClient()
            conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            conn.connect( parPOOL['host'], parPOOL['port'], parPOOL['user'], parPOOL['password'] )

            bashCOMMAND = f'echo successfully connected to {parPOOL["host"]}'
            stdin, stdout, stderr = conn.exec_command(bashCOMMAND)

            for line in stdout:
                self.general.LOG('LOG', 'asdfNAME', self.line.strip())

        except Exception as e:
            self.general.LOG('ExceptionRaised', f'Got Error {type(e)} : {e}')
        finally:
            if conn != None:
                conn.close()


#def PyModule_SSHCmder_CheckerFactory(loadDICT:dict):
#    par_pool = ParameterPoolFactory(loadDICT)
#    if loadDICT['Module'] == 'SSHCmder':
#        return PyModule_SSHCmder_Checker(loadDICT['CMDDetails'], par_pool)

class PyModule_SSHCmder_Run:
    def __init__(self, geneeralCMDER:PyModule_SSHCmder_general):
        self.general = generalCMDER
    def execute(self, parPOOL:ParameterPool):
        
