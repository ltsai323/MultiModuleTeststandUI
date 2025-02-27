import paramiko
import select
import time
import PythonTools.LoggingMgr as LoggingMgr
import PythonTools.threading_tools as threading_tools
from pprint import pprint
import JobModule.bashcmd as bashcmd
import JobModule.joborganization_base as joborganization_base
import yaml

DEBUG_MODE = True

def load_yaml(f):
    with open(f,'r') as fIN:
        return yaml.safe_load(fIN)
def delfunc(classOBJ, name):
    if hasattr(classOBJ, name):
        inst = getattr(classOBJ,name)
        if inst == None: return

        inst.Stop()
        delattr(classOBJ,name)
        setattr(classOBJ,name,None)
class JobOrganization(joborganization_base.JobOrganization_base):
    '''
    The example module that booking a job frag.
    '''
    def __init__(self):
        loadedYAMLdict = load_yaml('data/bashcmd_kriaenv.yaml')
        self.kriaenv       = bashcmd.YamlConfiguredJobFrag(loadedYAMLdict)
        loadedYAMLdict = load_yaml('data/bashcmd_daqclient.yaml')
        self.par_daqclient = bashcmd.YamlConfiguredJobFrag(loadedYAMLdict)
        loadedYAMLdict = load_yaml('data/bashcmd_takedata.yaml')
        self.ser_takedata  = bashcmd.YamlConfiguredJobFrag(loadedYAMLdict)
    def __del__(self):
        delfunc(self, 'ser_takedata')
        delfunc(self, 'par_daqclient')
        delfunc(self, 'kriaenv')


    def Initialize(self):
        self.kriaenv.Initialize()
        time.sleep(0.5)
        if not hasattr(self, 'bkg_threads') or getattr(self, 'bkg_threads') != None: ### need to check bkg_threads is None or not. asdf
            self.bkg_thread = threading_tools.ThreadingTools(self.par_daqclient.Initialize)
            self.bkg_thread.BkgRun()
        else:
            raise RuntimeError(f'[DuplicatedInitializing] the background process activated twice because Initialize() called twice.')
        self.ser_takedata.Initialize()

    def Configure(self, updatedCONF:dict) -> bool:
        return
        # TBD
        is_configured = self.testssh.Configure(updatedCONF['kriaenv'])
        return is_configured
    def ShowAllConfigurations(self) -> dict:
        return { 'kriaenv': self.kriaenv.show_configurations() } ## TBD


    def Run(self):
        self.kriaenv.Run()


        time.sleep(3)
        self.par_daqclient.Run()
        time.sleep(0.5)
        self.ser_takedata.Run()
        print('\n\n\n[RUN FINISHED] asldkjfaslkdfjalskdfjaskldf\n\n\n')
        
        
        ### no need to delete the background running daqclient
        
        

    def Stop(self):
        self.ser_takedata.Stop()
        self.par_daqclient.Stop()

        self.kriaenv.Stop()



def test_YamlConfiguredJobOrganization():
    moduletest = JobOrganization()

    moduletest.Initialize()
    #moduletest.Configure( {'': {'prefix': 'configured'} } )
    print('\n\n\n[PROC] Run start\n\n\n')
    moduletest.Run()
    print('\n\n\n[PROC] Run FINISHED\n\n\n')
    pprint(moduletest.ShowAllConfigurations())



    





if __name__ == "__main__":
    test_YamlConfiguredJobOrganization()
