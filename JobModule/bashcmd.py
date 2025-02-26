import threading
import time
import subprocess
import JobModule.jobfrag_base as jobfrag_base
import PythonTools.LoggingMgr as LoggingMgr
import logging




### main function
def run_bash_cmd_at_background(command:str, mergeSTDERRandSTDOUT=True):
    if mergeSTDERRandSTDOUT:
        ### merge stdout and stderr
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1, shell=True)
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1, shell=True)
    return process

def get_output(log, pipeMESG, mesgCOUNTER = 0):
    mesgCOUNTER = 0
    for line in iter(pipeMESG.readline, b''):
        log.info(line.decode().rstrip())
        mesgCOUNTER += 1 # when mesg received, +1. Such as the outside function is able to check whether NO ANY MESSAGE from pipe message
    log.debug(f'[counter] get_output() got {mesgCOUNTER} messages')

def get_output_withtimeout(log, pipeMESG, timeout = 2):
    if timeout < 0: # if timeout not set. waiting for the pipe ended
        get_output(log,pipeMESG)
        return

    timeout_stamp = 0
    thread = threading.Thread(target=get_output, args=(log,pipeMESG, timeout_stamp))
    thread.start()
    while True:
        tmp_timeout_stamp = timeout_stamp
        time.sleep(timeout)
        if thread.is_alive():
            if tmp_timeout_stamp == timeout_stamp: # not flip: show timeout
                log.warning(f'[TIMOUT] BashCMD got a timeout in {timeout} second')
        else:
            break
    thread.join()

            
            
            


def terminate_the_process(proc, log, timeOUT=2):
    if proc == None: return

    log.info(f'[TerminateBashCMD] Terminating this job')
    proc.terminate()
    time.sleep(0.7)
    # If the process terminated. return
    if proc.poll() is not None: return
    log.info(f'[TerminateBashCMD] Terminating takes time, waiting for timer {timeOUT} second')

    # if the process is still running, waiting for timeout
    time.sleep(timeOUT)
    if proc.poll() is not None: return
    log.info(f'[TerminateBashCMD] Job cannot terminate in {timeout} second, force kill it')

    # if the process is still running, force kill the process and waiting for eneded
    proc.kill()
    if proc.poll() is None: process.wait()
    log.info(f'[TerminateBashCMD] Force killed job')
    return

    



def testfunc_directrun_bkgrun_and_kill():
    proc = run_bash_cmd_at_background('echo aaaaaa && sleep 5 && echo a2 && sleep 5 && echo finished')
    thread = threading.Thread(target=get_output, args=(logging,proc.stdout))
    thread.start()

    time.sleep(10)
    print('[after sleep] kill job')
    terminate_the_process(proc, logging)
    print('[after sleep] job killed')
    thread.join()

    print('[FINISHED] the job success finished')
    exit()
def testfunc_directrun():
    proc = run_bash_cmd_at_background('echo aaaaaa && sleep 5 && echo a2 && sleep 5 && echo finished', True)
    get_output(logging,proc.stdout)
    print('[FINISHED] the job success finished')
    exit()
def testfunc_directrun_showerr():
    proc = run_bash_cmd_at_background('echo aaaaaa && aslkdfjs ; echo hi && sleep 5 && echo a2 && sleep 5 && echo finished', False)
    get_output(logging,proc.stderr)
    print('[FINISHED] the job success finished')
    exit()
def testfunc_directrun_withtimeout():
    proc = run_bash_cmd_at_background('echo aaaaaa && sleep 5 && echo a2 && sleep 5 && echo finished', True)
    get_output_withtimeout(logging,proc.stdout, 2)
    print('[FINISHED] the job success finished')
    exit()
def testfunc_directrun_usingLoggingMgr():
    stdout_err_mesg_filter = LoggingMgr.ErrorMessageFilter()
    stderr_err_mesg_filter = LoggingMgr.ErrorMessageFilter( [
            LoggingMgr.errortype('Type1Err', 0, '[running] 1'),
            LoggingMgr.errortype('Type3Err', 0, '[running] 3'),
        ])
    #global log_stdout, log_stderr
    log_stdout = LoggingMgr.configure_logger('out', 'log_stdout.txt', stdout_err_mesg_filter)
    log_stderr = LoggingMgr.configure_logger('err', 'log_stderr.txt', stderr_err_mesg_filter)



    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    
    pkey = get_private_key(log_stdout.info,'/Users/noises/.ssh/toNTU8')
    ssh_client.connect(hostname="ntugrid8.phys.ntu.edu.tw", username="ltsai", pkey = pkey)

    command = 'python3 -u main_job.py'
    #command = 'python3 -u main_job.py 1>&2'
    #command = 'sh main_job.sh 1>&2'
    execute_command_with_timeout(ssh_client, log_stdout, log_stderr, command, timeout=1)

    log_stdout.info('SSH client closed')
    ssh_client.close()
    log_stdout.info('end of test_direct_run()')



''' ------------------------------------- packing functions ------------------------------------- '''
import JobModule.jobfrag_base as jobfrag_base
class JobFrag(jobfrag_base.JobFragBase):
    def __init__(self,  jobTIMEOUT:float,
                 stdOUT, stdERR,
                 cmdTEMPLATEs:dict, argCONFIGs:dict, argSETUPs:dict):

        self.job_timeout = jobTIMEOUT

        self.log = stdOUT
        self.err = stdERR

        self.set_cmd_template(cmdTEMPLATEs)
        self.set_config(argCONFIGs)
        self.set_config_const(argSETUPs)

        self.proc = None
    def __del__(self):
        self.log.debug('[BashCMD] __del__() destroy everything.')
        if self.proc is not None:
            terminate_the_process(self.proc, 2) # terminate job using 2 second timeout
        self.log.debug('[BashCMD] __del__() destroy everything accomplished.')

    def Initialize(self):
        cmd = self.get_full_command_from_cmd_template('init')
        if cmd != '':
            proc = run_bash_cmd_at_background(cmd, False)
            get_output(self.log,proc.stdout)
        self.log.debug('[BashCMD] Initialize() finished')
        ''' bash command needs no checking '''
        pass
    def Configure(self, updatedCONF:dict) -> bool:
        '''
        Update old argument config only if all configs in old argument config being confirmed.
        If there are some redundant key - value pair in updatedCONF, these configs are ignored.

        updatedCONF: dict. It should have the same format with original arg config
        '''
        for key, value in updatedCONF.items():
            error_mesg = self.set_config_value(key,value)
            if error_mesg:
                self.err.warning(f'[{error_mesg}] Invalid configuration from config: key "{ key }" and value "{ value }".')
                return False
        return True


        
    def Run(self):
        self.log.debug(f'[BashCMD] Run() start running cmd')

        cmd = self.get_full_command_from_cmd_template('run')
        if cmd == '': raise RuntimeError(f'[BashCMD] No any bash command found in Run()')

        proc = run_bash_cmd_at_background(cmd, False)
        get_output_withtimeout(self.log,proc.stdout, self.job_timeout)
        self.log.debug(f'[BashCMD] Run() running finished')


    def Stop(self):
        self.log.debug(f'[BashCMD] Stop() terminating job')
        if self.proc is not None:
            terminate_the_process(self.proc, 10) # terminate job using 10 second timeout

        cmd = self.get_full_command_from_cmd_template('stop')
        if cmd != '':
            proc = run_bash_cmd_at_background(cmd, False)
            get_output(self.log,proc.stdout)
        self.log.debug(f'[BashCMD] Stop() job terminated')

def testfunc_pack_JobFrag():
    logger = logging
    timeout = -1
    cmd_template = {
        'init': 'echo initialinggg',
        'run': 'echo RUNNING CMD && echo aaaaaa && aslkdfjs ; echo hi && sleep 5 && echo a2 && sleep 5 && echo finished',
        'stop': 'echo stoppinggg',
        'del': 'echo deleting..'
    }
    arg_config = {
        'prefix': 'default',
    }
    arg_const_config = {
            'ip2': 'ntugrid5.phys.ntu.edu.tw'
    }



    job = JobFrag(
            jobTIMEOUT = timeout,
            stdOUT = logger, stdERR = logger,
            cmdTEMPLATEs = cmd_template, argCONFIGs = arg_config, argSETUPs = arg_const_config
    )

    job.Initialize()
    job.Run()
    job.Stop()


def YamlConfiguredJobFrag(yamlLOADEDdict:dict):
    config = yamlLOADEDdict
    try:
        #### configure the status output
        log_stdout, log_stderr = LoggingMgr.YamlConfiguredLoggers(config['logging'])

        basic_pars = config['basic_parameters']
        cmd_templates = config['cmd_templates']
        cmd_arguments = config['cmd_arguments']
        cmd_const_arguments = config['cmd_const_arguments']
        job_frag = JobFrag(
                basic_pars['timeout'],
                log_stdout, log_stderr,
                cmd_templates, cmd_arguments, cmd_const_arguments
        )
    except KeyError as e:
        raise KeyError(f'Invalid key in yaml config "{ config }"') from e

    return job_frag
def test_YamlConfiguredJobFrag():
    yaml_content = '''
basic_parameters:
    timeout: -1
cmd_templates:
  'init': 'echo initialinggg'
  'run': 'echo "configured command={prefix}. The contain should be configured if Confiugred() and default is default" &&  echo RUNNING CMD && echo aaaaaa && aslkdfjs ; echo hi && sleep 5 && echo a2 && sleep 5 && echo finished'
  'stop': 'echo stoppinggg'
  'del': 'echo deleting..'
cmd_arguments:
  prefix: default
cmd_const_arguments:
  ip2: ntugrid5.phys.ntu.edu.tw
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
        print(f'[ExportedYamlFile] yaml file the_conf.yaml saved')
    import yaml
    with open('the_conf.yaml','r') as f:
        loaded_conf = yaml.safe_load(f)

    job_frag = YamlConfiguredJobFrag(loaded_conf)
    job_frag.Initialize()
    job_frag.Configure( {'prefix': 'confiugred'} )
    job_frag.Run()
    job_frag.Stop()




if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logging.info('bash cmd startting')
    #testfunc()
    #testfunc_directrun()
    #testfunc_directrun_showerr()
    #testfunc_directrun_withtimeout()
    #testfunc_directrun_bkgrun_and_kill()
    #testfunc_pack_JobFrag()
    test_YamlConfiguredJobFrag()
