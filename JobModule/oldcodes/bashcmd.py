import threading
import time
import subprocess
import JobModule.jobfrag_base as jobfrag_base
import PythonTools.LoggingMgr as LoggingMgr
import logging
from PythonTools.threading_tools import ThreadingTools




### main function
def run_bash_cmd_at_background(command:str, mergeSTDERRandSTDOUT=True):
    if mergeSTDERRandSTDOUT:
        ### merge stdout and stderr
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1, shell=True)
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1, shell=True)
    return process
def process_is_alive(thePROCESS):
    if thePROCESS is None: return False
    print(f'[check_process] process {thePROCESS}')
    return True if thePROCESS.poll() is None else False

def get_output(log, pipeMESG, mesgCOUNTER = 0, extTERMINATING = threading.Event()):
    mesgCOUNTER = 0
    for line in iter(pipeMESG.readline, b''):
        log.info(line.decode().rstrip())
        mesgCOUNTER += 1 # when mesg received, +1. Such as the outside function is able to check whether NO ANY MESSAGE from pipe message
        if extTERMINATING.is_set(): break
    log.debug(f'[counter] get_output() got {mesgCOUNTER} messages')

def get_output_withtimeout(log, bkgPROC, timeout = 2, stopTRIG=threading.Event()):
    pipeMESG = bkgPROC.stdout
    if timeout <= 0: # if timeout not set. waiting for the pipe ended
        get_output(log,pipeMESG)
        return

    SEP = 4 if timeout > 4 else 1
    SEP_TIMEOUT = int(timeout/SEP)

    timeout_record = 0
    ext_terminating = threading.Event()
    getmesg = threading.Thread(target=get_output, args=(log,pipeMESG, timeout_record, ext_terminating))
    getmesg.start()

    ### terminate_loop is  ( bkgPROC finished || stopTRIG set )
    terminate_loop = False
    asdfasdf = 10
    while True: ## timeout looping
        tmp_timeout_record = timeout_record
        for i in range(SEP): # separate the whole timeout in 4 times. check the code finished or not
            time.sleep(SEP_TIMEOUT)

            process_alive = process_is_alive(bkgPROC)
            getmesg_alive = getmesg.is_alive()


            if getmesg_alive and process_alive:
                pass
            else:
                log.debug(f'[JobTermiated] get_output_withtimeout() is terminated due to getmesg.is_alive({getmesg.is_alive()})  or bkgPROC is alive ({process_is_alive(bkgPROC)}) is not None')
                terminate_loop = True
                break
        if tmp_timeout_record == timeout_record: # if timeout_record does not change value: show timeout
            log.warning(f'[TIMOUT] BashCMD got a timeout in {timeout} second')
            log.debug(f'[TIMOUT] BashCMD got a timeout in {timeout} second and current message : bkgPROC is alive ({process_is_alive(bkgPROC)}) and getmesg_alive({getmesg.is_alive()})')

        asdfasdf -= 1
        log.debug(f'[selfTerminator] counter {asdfasdf}')
        if asdfasdf < 0:
            log.debug(f'[selfTerminator] self stop triggered!')
            terminate_loop = True

        if stopTRIG.is_set(): terminate_loop = True
        if terminate_loop:
            log.debug(f'[TerminateLoop] Received termination in get_output_withtimeout(). Terminating the looping...')
            ext_terminating.set() ## kill get_message
            terminate_the_process(bkgPROC, log, 2) ## kill process
            stopTRIG.set()
            break ## kill timeout looping
    return



def terminate_the_process(proc, log, timeOUT=2):
    if proc == None: return

    log.info(f'[TerminateBashCMD] Terminating this job')
    proc.terminate()
    time.sleep(0.7)
    log.debug(f'[terminate_the_process] process is still alive ? {process_is_alive(proc)}')

    # If the process terminated. return
    if not process_is_alive(proc): return
    log.info(f'[TerminateBashCMD] Terminating takes time, waiting for timer {timeOUT} second')

    # if the process is still running, waiting for timeout
    time.sleep(timeOUT)
    if not process_is_alive(proc): return
    log.info(f'[TerminateBashCMD] Job cannot terminate in {timeout} second, force kill it')

    # if the process is still running, force kill the process and waiting for eneded
    proc.kill()
    if not process_is_alive(proc): return
    log.info(f'[TerminateBashCMD] Force killed job')
    return

    



def testfunc_directrun_bkgrun_and_kill():
    proc = run_bash_cmd_at_background('echo aaaaaa && sleep 10 && echo finisehd')
    stop_trig = threading.Event()
    thread = threading.Thread(target=get_output, args=(logging,proc.stdout, stop_trig))
    thread.start()

    time.sleep(1)
    print('[after sleep] kill job')
    stop_trig.set()
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
    get_output_withtimeout(logging,proc, 2)
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
                 templateCMDinit:str,
                 templateCMDdel:str,
                 templateCMDrun:str,
                 templateCMDstop:str,
                 argCONFIGs:dict, constargCONFIGs:dict,
                 stdOUT, stdERR,
                 ):
        cmdTEMPLATEs = {
                'init': templateCMDinit,
                'del' : templateCMDdel,
                'run' : templateCMDrun,
                'stop': templateCMDstop,
        }
        
        super(JobFrag,self).__init__( cmdTEMPLATEs, argCONFIGs, constargCONFIGs, stdOUT,stdERR )

        self.job_timeout = jobTIMEOUT

        self.proc = None
    def __del__(self):
        print('[BashCMD] __del__() destroy everything.')
        #self.log.debug('[BashCMD] __del__() destroy everything.')
        if self.proc is not None:
            terminate_the_process(self.proc, self.log, 2) # terminate job using 2 second timeout

        #cmd = self.get_full_command_from_cmd_template('stop')
        #if cmd != '':
        #    proc = run_bash_cmd_at_background(cmd, False)
        #    get_output(self.log,proc.stdout)

        cmd = self.get_full_command_from_cmd_template('del')
        if cmd != '':
            proc = run_bash_cmd_at_background(cmd, False)
            get_output(self.log,proc.stdout)
        self.log.debug('[BashCMD] __del__() destroy everything accomplished.')

    def Initialize(self, stopTRIG=threading.Event()):
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
            error_mesg = self.set_value_to_config(key,value)
            if error_mesg:
                self.err.warning(f'[{error_mesg}] Invalid configuration from config: key "{ key }" and value "{ value }".')
                return False
        return True


        
    def Run(self, stopTRIG=threading.Event()):
        self.log.debug(f'[BashCMD] Run() start running cmd')

        cmd = self.get_full_command_from_cmd_template('run')
        if cmd == '':
            self.log.debug(f'[BashCMD] Run() start running but NO ANY COMMAND FOUND')
            return  # not to raise run time error
            raise RuntimeError(f'[BashCMD] No any bash command found in Run()')

        proc = run_bash_cmd_at_background(cmd, False)
        get_output_withtimeout(self.log,proc, self.job_timeout, stopTRIG)
        self.log.debug(f'[BashCMD] Run() running finished')


    def Stop(self):
        self.log.debug(f'[BashCMD] Stop() terminating job')
        if self.proc is not None:
            terminate_the_process(self.proc, self.log, 10) # terminate job using 10 second timeout

        cmd = self.get_full_command_from_cmd_template('stop')
        if cmd != '':
            proc = run_bash_cmd_at_background(cmd, False)
            get_output(self.log,proc.stdout)
        self.log.debug(f'[BashCMD] Stop() job terminated')
        if self.proc == None:
            self.log.debug(f'[BashCMD] Stop() status. self.proc is None')
        else:
            self.log.debug(f'[BashCMD] Stop() status. self.proc is running ? {process_is_alive(self.proc)}')

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
                templateCMDinit = cmd_template['init'],
                templateCMDdel  = cmd_template['del' ],
                templateCMDrun  = cmd_template['run' ],
                templateCMDstop = cmd_template['stop'],
                argCONFIGs=arg_config,constargCONFIGs=arg_const_config,
                stdOUT=logger, stdERR=logger
        )

    print('\n\n>>>>>>>>>>>\nA INITIALIZE <<<<<<<<<<\n\n')
    job.Initialize()
    print('\n\n>>>>>>>>>>>\nA RUN        <<<<<<<<<<\n\n')
    job.Run()
    print('\n\n>>>>>>>>>>>\nA STOP       <<<<<<<<<<\n\n')
    job.Stop()
    print('\n\n>>>>>>>>>>>\nA DEL        <<<<<<<<<<\n\n')
    del job
    print('\n\n>>>>>>>>>>>\nA END        <<<<<<<<<<\n\n')


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
                templateCMDinit = cmd_templates['init'],
                templateCMDdel  = cmd_templates['del' ],
                templateCMDrun  = cmd_templates['run' ],
                templateCMDstop = cmd_templates['stop'],
                argCONFIGs=cmd_arguments,constargCONFIGs=cmd_const_arguments,
                stdOUT=log_stdout,stdERR=log_stderr,
        )
    except KeyError as e:
        raise KeyError(f'Invalid key in yaml config "{ config }"') from e

    return job_frag
def testfunc_default_yaml_config():
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
        print(f'[YamlExport] testfunc_default_yaml_config() generates a default yaml file: the_conf.yaml')
    exit()

def testfunc_YamlConfiguredJobFrag( inFILE ):
    import yaml
    with open(inFILE,'r') as f:
        loaded_conf = yaml.safe_load(f)

    job_frag = YamlConfiguredJobFrag(loaded_conf)
    print('\n\n>>>>>>>>>>> INITIALIZE <<<<<<<<<<\n\n')
    job_frag.Initialize()
    job_frag.Configure( {'prefix': 'confiugred'} )
    print('\n\n>>>>>>>>>>> RUN        <<<<<<<<<<\n\n')
    job_frag.Run()
    print('\n\n>>>>>>>>>>> STOP       <<<<<<<<<<\n\n')
    job_frag.Stop()
    print('\n\n>>>>>>>>>>> DEL        <<<<<<<<<<\n\n')
    #del job_frag
    print('\n\n>>>>>>>>>>> END        <<<<<<<<<<\n\n')
    exit()

def testfunc_YamlConfiguredJobFrag_with_termination( inFILE ):
    import yaml
    with open(inFILE,'r') as f:
        loaded_conf = yaml.safe_load(f)

    job_frag = YamlConfiguredJobFrag(loaded_conf)
    print('\n\n>>>>>>>>>>> INITIALIZE <<<<<<<<<<\n\n')
    job_frag.Initialize()
    job_frag.Configure( {'prefix': 'confiugred'} )
    print('\n\n>>>>>>>>>>> RUN        <<<<<<<<<<\n\n')
    ext_term = threading.Event()
    bkg_run_thread = ThreadingTools(job_frag.Run, ext_term)
    bkg_run_thread.BkgRun()
    time.sleep(5)
    print('\n\n>>>>>>>>>>> STOP in 2s <<<<<<<<<<\n\n')
    #job_frag.Stop()
    ext_term.set()
    print(f'ext trigger set!')
    print('\n\n>>>>>>>>>>> END        <<<<<<<<<<\n\n')
    time.sleep(10)
    exit()



if __name__ == "__main__":
    import sys
    #testfunc_default_yaml_config()
    #testfunc_YamlConfiguredJobFrag(sys.argv[1])
    #testfunc_YamlConfiguredJobFrag_with_termination(sys.argv[1])

    # for directly run
    logging.basicConfig(level=logging.DEBUG)

    logging.info('bash cmd startting')
    #testfunc()
    #testfunc_directrun()
    #testfunc_directrun_showerr()
    #testfunc_directrun_withtimeout()
    #testfunc_directrun_bkgrun_and_kill()
    testfunc_pack_JobFrag()
