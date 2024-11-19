import paramiko
import threading
import select
import time
import LoggingMgr
from pprint import pprint
import jobinstance_sshconn

DEBUG_MODE = True




def YamlConfiguredJobUnit(yamlLOADEDdict):
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
        job_unit = jobinstance_sshconn.JobUnit(
                basic_pars['host'], basic_pars['user'], basic_pars['pkey'], basic_pars['timeout'],
                log_stdout, log_stderr,
                cmd_templates, cmd_arguments
        )
    except KeyError as e:
        raise KeyError(f'Invalid key in yaml config "{ config }"') from e

    return job_unit
def test_YamlConfiguredJobUnit():
    yaml_content = '''
basic_parameters:
  timeout: 0.4
  host: 'ntugrid8.phys.ntu.edu.tw'
  user: 'ltsai'
  pkey: '/Users/noises/.ssh/toNTU8'
cmd_templates:
  'init': 'echo "connection established"'
  'run': 'python3 -u main_job.py; echo "config: {prefix}"'
  'stop': 'exit'
cmd_arguments:
  prefix: default
logging:
  stdout:
    name: out
    file: log_stdout.txt
    filters:
      - indicator: running
        threshold: 0
        pattern: 'RUNNING'
        filter_method: exact
      - indicator: Type0ERROR
        threshold: 0
        pattern: '[running] 0'
        filter_method: exact
      - indicator: Type3ERROR
        threshold: 0
        pattern: '[running] 3'
        filter_method: contain
      - indicator: idle
        threshold: 0
        pattern: 'FINISHED'
        filter_method: exact
  stderr:
    name: err
    file: log_stderr.txt
    filters:
      - indicator: running
        threshold: 0
        pattern: 'RUNNING'
        filter_method: exact
      - indicator: Type0ERROR
        threshold: 0
        pattern: '[running] 0'
        filter_method: exact
      - indicator: RaiseError
        threshold: 0
        pattern: 'Error'
        filter_method: contain
        '''

    with open('the_conf.yaml','w') as f:
        f.write(yaml_content)
    import yaml
    with open('the_conf.yaml','r') as f:
        loaded_conf = yaml.safe_load(f)

    job_unit = YamlConfiguredJobUnit(loaded_conf)
    job_unit.Initialize()
    job_unit.Configure( {'prefix': 'confiugred'} )
    job_unit.Run()


    





if __name__ == "__main__":
    #test_jobconfigure()
    test_YamlConfiguredJobUnit()
    #testfunc()
