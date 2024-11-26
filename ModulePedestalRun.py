import paramiko
import threading
import select
import time
import LoggingMgr
from pprint import pprint
import jobinstance_sshconn
import ModuleBase

DEBUG_MODE = True

def pack_function_to_bkg_exec(func):
    t = threading.Thread()
    t = threading.Thread(target=func,)
    t.start()
    return t

def waiting_for_thread_finished(t):
    while t.is_alive():
        time.sleep(1.0)





class ModuleExample_2sshconnection(ModuleBase.ModuleBase):
    '''
    The example module that booking 2 ssh job instance.
    '''
    def __init__(self, yamlLOADEDdict:dict):
        self.cmdPC   = jobinstance_sshconn.YamlConfiguredJobInstance(yamlLOADEDdict['cmdPC'])
        self.hexCtrl = jobinstance_sshconn.YamlConfiguredJobInstance(yamlLOADEDdict['hexCtrl'])
    def __del__(self):
        self.cmdPC.Stop()
        self.hexCtrl.Stop()
        del self.cmdPC
        del self.hexCtrl

    def Initialize(self):
        self.cmdPC  .Initialize()
        self.hexCtrl.Initialize()

    def Configure(self, updatedCONF:dict):
        self.cmdPC  .Configure(updatedCONF['cmdPC'  ])
        self.hexCtrl.Configure(updatedCONF['hexCtrl'])
    def show_configurations(self) -> dict:
        return { 'cmdPC': self.cmdPC.show_configurations(), 'hexCtrl': self.hexCtrl.show_configurations() }

    def Run(self):
        # Put self.ssh_check.Run() in background
        t_check = pack_function_to_bkg_exec(self.ssh_check.Run)
        self.ssh_job.Run()

        # waiting for job finished, terminate ssh_check.Run()
        self.ssh_check.Stop()
        waiting_for_thread_finished(t_check)

        

    def Stop(self):
        self.cmdPC.Stop()
        #self.hexCtrl.Stop() # no need to destroy 



def test_YamlConfiguredModuleExample():
    import yaml
    with open('data/modulepedestal_run.yaml','r') as f:
        loaded_conf = yaml.safe_load(f)

    moduletest = ModuleExample_2sshconnection(loaded_conf)

    moduletest.Initialize()
    #moduletest.Configure( {'ntu8_test': {'prefix': 'configured'} } )
    moduletest.Run()

if __name__ == "__main__":
    test_YamlConfiguredModuleExample()
