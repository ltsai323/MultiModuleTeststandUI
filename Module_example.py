import paramiko
import threading
import select
import time
import LoggingMgr
from pprint import pprint
import jobinstance_sshconn
import ModuleBase

DEBUG_MODE = True

class Module_example(ModuleBase.ModuleBase):
    '''
    The example module that booking a job instance.
    '''
    def __init__(self, yamlLOADEDdict:dict):
        self.sshconn = jobinstance_sshconn.YamlConfiguredJobInstance(yamlLOADEDdict['ntu8_test'])

    def Initialize(self):
        self.sshconn.Initialize()

    def Configure(self, updatedCONF:dict):
        self.sshconn.Configure(updatedCONF['ntu8_test'])

    def Run(self):
        self.sshconn.Run()

    def Stop(self):
        self.sshconn.Stop()

    def Destroy(self):
        self.sshconn.Stop()



def test_YamlConfiguredModuleExample():
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
#    logging:
#      stdout:
#        name: out
#        file: log_stdout.txt
#        filters:
#          - indicator: running
#            threshold: 0
#            pattern: 'RUNNING'
#            filter_method: exact
#          - indicator: Type0ERROR
#            threshold: 0
#            pattern: '[running] 0'
#            filter_method: exact
#          - indicator: Type3ERROR
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
#          - indicator: Type0ERROR
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
    with open('data/module_example.yaml','r') as f:
        loaded_conf = yaml.safe_load(f)

    moduletest = Module_example(loaded_conf)

    moduletest.Initialize()
    moduletest.Configure( {'ntu8_test': {'prefix': 'configured'} } )
    moduletest.Run()


    





if __name__ == "__main__":
    test_YamlConfiguredModuleExample()
