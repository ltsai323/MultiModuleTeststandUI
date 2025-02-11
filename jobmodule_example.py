import paramiko
import threading
import select
import time
import LoggingMgr
from pprint import pprint
import jobfrag_sshconn
import jobmodule_base

DEBUG_MODE = True

class JobModuleExample(jobmodule_base.JobModule_base):
    '''
    The example module that booking a job frag.
    '''
    def __init__(self, yamlLOADEDdict:dict):
        self.sshconn = jobfrag_sshconn.YamlConfiguredJobFrag(yamlLOADEDdict['ntu8_test'])
    def __del__(self):
        self.sshconn.Stop()
        del self.sshconn

    def Initialize(self):
        self.sshconn.Initialize()

    def Configure(self, updatedCONF:dict) -> bool:
        is_configured = self.sshconn.Configure(updatedCONF['ntu8_test'])
        return is_configured
    def show_configurations(self) -> dict:
        return { 'ntu8_test': self.sshconn.show_configurations() }


    def Run(self):
        self.sshconn.Run()

    def Stop(self):
        self.sshconn.Stop()



def test_YamlConfiguredJobModuleExample():
#    yaml_content = '''
#ntu8_test:
#    basic_parameters:
#      timeout: 0.4
#      host: 'ntugrid8.phys.ntu.edu.tw'
#      user: 'ltsai'
#      pkey: '/Users/noises/.ssh/toNTU8'
#    cmd_templates:
#      'init': 'echo "connection established"'
#      'run': 'python3 -u main_job.py; echo "config: {prefix}"'
#      'stop': 'exit'
#    cmd_arguments:
#      prefix: default
#    cmd_const_arguments:
#      prefix2: default2
#    logging:
#      stdout:
#        name: out
#        file: log_stdout.txt
#        filters:
#          - indicator: running
#            threshold: 0
#            pattern: 'RUNNING'
#            filter_method: exact
#          - indicator: 'Type0ERROR'
#            threshold: 0
#            pattern: '[running] 0'
#            filter_method: exact
#          - indicator: 'Type3ERROR'
#            threshold: 0
#            pattern: '[running] 3'
#            filter_method: contain
#          - indicator: idle
#            threshold: 0
#            pattern: 'FINISHED'
#            filter_method: exact
#      stderr:
#        name: err
#        file: log_stderr.txt
#        filters:
#          - indicator: running
#            threshold: 0
#            pattern: 'RUNNING'
#            filter_method: exact
#          - indicator: 'Type0ERROR'
#            threshold: 0
#            pattern: '[running] 0'
#            filter_method: exact
#          - indicator: RaiseError
#            threshold: 0
#            pattern: 'Error'
#            filter_method: contain
#        '''
#
#    with open('the_conf.yaml','w') as f:
#        f.write(yaml_content)
#    import yaml
#    with open('the_conf.yaml','r') as f:
#        loaded_conf = yaml.safe_load(f)
    import yaml
    with open('data/moduleexample.yaml','r') as f:
        loaded_conf = yaml.safe_load(f)

    moduletest = JobModuleExample(loaded_conf)

    moduletest.Initialize()
    moduletest.Configure( {'ntu8_test': {'prefix': 'configured'} } )
    moduletest.Run()
    pprint(moduletest.show_configurations())


    





if __name__ == "__main__":
    test_YamlConfiguredJobModuleExample()
