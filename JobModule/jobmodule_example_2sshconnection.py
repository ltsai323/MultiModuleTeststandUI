import paramiko
import threading
import select
import time
import LoggingMgr
from pprint import pprint
#import jobfrag_sshconn
#import jobmodule_base
import JobModule.jobfrag_sshconn as jobfrag_sshconn
import JobModule.jobmodule_base  as jobmodule_base 

DEBUG_MODE = True

def pack_function_to_bkg_exec(func):
    t = threading.Thread()
    t = threading.Thread(target=func,)
    t.start()
    return t

def waiting_for_thread_finished(t):
    while t.is_alive():
        time.sleep(1.0)


'''
def YamlConfiguredJobFrag(yamlLOADEDdict):
    config = yamlLOADEDdict
    try:
        #### configure the status output
        log_config = config['logging']['stdout']
        stdout_filter_rules = [ LoggingMgr.errortype_factory(c['filter_method'], c['indicator'],c['threshold'],c['pattern']) for c in log_config['filters'] ]
        stdout_filter = LoggingMgr.ErrorMessageFilter(stdout_filter_rules)
        log_stdout = LoggingMgr.configure_logger(log_config['name'],log_config['file'], stdout_filter)

        log_config = config['logging']['stderr']
        stderr_filter_rules = [ LoggingMgr.errortype_factory(c['filter_method'], c['indicator'],c['threshold'],c['pattern']) for c in log_config['filters'] ]
        stderr_filter = LoggingMgr.ErrorMessageFilter(stderr_filter_rules)
        log_stderr = LoggingMgr.configure_logger(log_config['name'],log_config['file'], stderr_filter)

        basic_pars = config['basic_parameters']
        cmd_templates = config['cmd_templates']
        cmd_arguments = config['cmd_arguments']
        job_unit = jobfrag_sshconn.JobFrag(
                basic_pars['host'], basic_pars['user'], basic_pars['pkey'], basic_pars['timeout'],
                log_stdout, log_stderr,
                cmd_templates, cmd_arguments
        )
    except KeyError as e:
        raise KeyError(f'Invalid key in yaml config "{ config }"') from e

    return job_unit
import threading
def pack_function_to_bkg_exec(func):
    t = threading.Thread()
    t = threading.Thread(target=func,)
    t.start()
    return t
    
    
def test_YamlConfiguredJobFrag():
    infile1 = 'data/example_2sshconn_1.yaml'
    infile2 = 'data/example_2sshconn_2.yaml'
    import yaml

    with open(infile1,'r') as f:
        loaded_conf1 = yaml.safe_load(f)
    job_unit1 = YamlConfiguredJobFrag(loaded_conf1)
    with open(infile2,'r') as f:
        loaded_conf2 = yaml.safe_load(f)
    job_unit2 = YamlConfiguredJobFrag(loaded_conf2)

    job_unit2.Initialize()
    job_unit2.Configure( {'prefix': 'confiugred'} )

    t = pack_function_to_bkg_exec(job_unit2.Run)
    #job_unit2.Run()

    # Monitor threads
    idx = 5
    while t.is_alive():
        print("Jobs are still running...")
        time.sleep(2.0)
        idx -= 1
        if idx < 0:
            job_unit2.Stop()
            print('stop sent')

    t.join()
'''




class JobModuleExample_2sshconnection(jobmodule_base.JobModule_base):
    '''
    The example module that booking 2 ssh job frag.
    '''
    def __init__(self, yamlLOADEDdict:dict):
        self.ssh_check = jobfrag_sshconn.YamlConfiguredJobFrag(yamlLOADEDdict['ntu8_check'])
        self.ssh_job   = jobfrag_sshconn.YamlConfiguredJobFrag(yamlLOADEDdict['ntu8_job'])
    def __del__(self):
        self.ssh_check.Stop()
        self.ssh_job  .Stop()
        del self.ssh_check
        del self.ssh_job

    def Initialize(self):
        self.ssh_check.Initialize()
        self.ssh_job.Initialize()

    def Configure(self, updatedCONF:dict):
        self.ssh_check.Configure(updatedCONF['ntu8_check'])
        self.ssh_job  .Configure(updatedCONF['ntu8_job'])
    def show_configurations(self) -> dict:
        return { 'ntu8_check': self.ssh_check.show_configurations() ,'ntu8_job'  : self.ssh_job  .show_configurations() }

    def Run(self):
        # Put self.ssh_check.Run() in background
        t_check = pack_function_to_bkg_exec(self.ssh_check.Run)
        self.ssh_job.Run()

        # waiting for job finished, terminate ssh_check.Run()
        self.ssh_check.Stop()
        waiting_for_thread_finished(t_check)

        

    def Stop(self):
        self.ssh_job  .Stop()
        self.ssh_check.Stop()


def JobModuleFactory(yamlFILE):
    import yaml
    with open(yamlFILE,'r') as f:
        loaded_conf = yaml.safe_load(f)

    return JobModuleExample_2sshconnection(loaded_conf)


def test_YamlConfiguredJobModuleExample():
    moduletest = JobModuleFactory('data/moduleexample_2sshconnection.yaml')

    moduletest.Initialize()
    moduletest.Configure( {'ntu8_job'  : {'prefix': 'configured'}, 'ntu8_check': {'asdklj':333} } )
    moduletest.Run()

    print(moduletest.show_configurations())


    del moduletest

if __name__ == "__main__":
    test_YamlConfiguredJobModuleExample()
