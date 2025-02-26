import paramiko
import threading
import select
import time
import PythonTools.LoggingMgr as LoggingMgr
from pprint import pprint
import JobModule.bashcmd as bashcmd
import JobModule.joborganization_base as joborganization_base
import yaml

DEBUG_MODE = True

def load_yaml(f):
    with open(f,'r') as fIN:
        return yaml.safe_load(fIN)
class JobOrganizationExample(joborganization_base.JobOrganization_base):
    '''
    The example module that booking a job frag.
    '''
    def __init__(self):
        loadedYAMLdict = load_yaml('data/bashcmd_default.yaml')
        self.testssh = bashcmd.YamlConfiguredJobFrag(loadedYAMLdict)
    def __del__(self):
        if hasattr(self, 'testssh'):
            if self.testssh != None:
                self.testssh.Stop()
                del self.testssh
                self.testssh = None


    def Initialize(self):
        self.testssh.Initialize()

    def Configure(self, updatedCONF:dict) -> bool:
        is_configured = self.testssh.Configure(updatedCONF['testssh'])
        return is_configured
    def ShowAllConfigurations(self) -> dict:
        return { 'testssh': self.testssh.show_configurations() }


    def Run(self):
        self.testssh.Run()

    def Stop(self):
        self.testssh.Stop()



def test_YamlConfiguredJobOrganizationExample():
    moduletest = JobOrganizationExample()

    moduletest.Initialize()
    moduletest.Configure( {'testssh': {'prefix': 'configured'} } )
    moduletest.Run()
    pprint(moduletest.ShowAllConfigurations())


    





if __name__ == "__main__":
    test_YamlConfiguredJobOrganizationExample()
