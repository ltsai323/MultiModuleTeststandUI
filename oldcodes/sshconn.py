import paramiko
import sys
import threading
import JobCMDPackManager
import queue
import time
import ConfigHandler
import JobStatManager
from DebugManager import BUG


def LOG(mesg:str):
    sys.stdout.write(mesg)


def get_private_key(logFUNC,privateKEY):
    try:
        return paramiko.RSAKey.from_private_key_file(privateKEY)
    except paramiko.SSHException:
        #logFUNC('[PrivateKeyNotFound]', f'Path "{privateKEY}" is not a valid private key')
        logFUNC(f'[PrivateKeyNotFound] Path "{privateKEY}" is not a valid private key')

### main function
def ssh_command(logFUNC,
                 terminateJOB:threading.Event,
                 sshCLIENT:paramiko.SSHClient,
                 command:str,
                 **connCONFIGs):
    connect_config = { 'hostname':connCONFIGs['hostname'], 'port':connCONFIGs['port'], 'username':connCONFIGs['username'], 'pkey':connCONFIGs['pkey'] }
    if not command or command == '': return
    ssh_client = sshCLIENT

    ssh_client.connect(**connect_config)
    #ssh_client.connect(hostname=hostname, port=port, username=username, pkey=pkey)
    logFUNC(f"Connected to {connect_config['hostname']}\n")

    # Execute the command
    stdin, stdout, stderr = ssh_client.exec_command(command)

    # Read and print the output
    while True:
        if terminateJOB.is_set():
            logFUNC('[ExternalTerminte]--- Terminate signal received! Trying to terminate job .....\n\n\n')
            break
        line = stdout.readline()
        if not line:
            break
        logFUNC(f'[stdout] {line}')

    if not terminateJOB.is_set():
        error = stderr.read().decode('utf-8')
        if error:
            logFUNC(f'[stderr] {error}')
    if terminateJOB.is_set():
        ssh_client.close()
    logFUNC('Finished')


class JobCMDPack(JobCMDPackManager.JobCMDPack):
    def __init__(self, name:str, jobtype:str, logQUEUE,
                 commandSET:ConfigHandler.LoadedCMDFactory,
                 loadedPARs:ConfigHandler.LoadedParameterFactory,
                 allCONFIGs:dict):
        super().__init__(name,jobtype,logQUEUE,loadedPARs)
        self.command_set = commandSET
        self.loaded_pars = loadedPARs
        self.all_configs = allCONFIGs
    def cmd(self, stagedCMD):
        return self.command_set.GetCMD(stagedCMD,self.GetParDict())
def JobCMDPackFactory(logQUEUE, yamlFILE:str) -> JobCMDPackManager.JobCMDPack:
    from tools.YamlHandler import YamlLoader
    loaded_configs = YamlLoader(yamlFILE)
    cmdTEMPLATE = loaded_configs.configs
    name = loaded_configs.configs['name']
    jobtype = loaded_configs.configs['jobtype']

    BUG(f'SSHCConn : JobCMDPackFactory loads configs : {loaded_configs}')
    parameters = ConfigHandler.LoadedParameterFactory(loaded_configs)
    configs = ConfigHandler.LoadedConfigFactory(loaded_configs)
    cmd_pool = ConfigHandler.LoadedCMDFactory(loaded_configs)

    return JobCMDPack(name,jobtype,logQUEUE,
        cmd_pool, parameters, configs)



def JobStatMgrFactory(jobtype, *args) -> JobStatManager.JobStatMgr:
    class JobStatMgr_BkgJobMonitor(JobStatManager.JobStatMgr_BkgJobMonitor):
        def __init__(self, newTHREAD, terminateJOB):
            self.thread = newTHREAD
            self.terminate_job = terminateJOB
        def terminate(self):
            self.terminate_job.set()
            self.thread.join() # wait until process finished
        def IsFinished(self):
            return self.thread.is_alive() == False
    class JobStatMgr_SequentialJob(JobStatManager.JobStatMgr_SequentialJob):
        def __init__(self, newTHREAD, terminateJOB):
            self.thread = newTHREAD
            self.terminate_job = terminateJOB
        def terminate(self):
            self.terminate_job.set()
            self.thread.join() # wait until process finished
        def IsFinished(self):
            return self.thread.is_alive() == False

    if jobtype == 'bkgjobmonitor':
        return JobStatMgr_BkgJobMonitor(*args)
    if jobtype == 'sequentialjob':
        return JobStatMgr_SequentialJob(*args)
    raise NotImplementedError(f'JobStatMgrFactory() : Invalid jobtype "{jobtype}". Check yaml file.')


## Checking the availablity is put at another code. (Init / Destroy)
def stage_cmd_initialize(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr, terminateJOBflag=threading.Event()):
    if hasattr(cmdPACK, 'ssh_client'):
        cmdPACK.RecordLog('[IgnoreInitialize] ssh_client was established before, ignore initialize')

    print('hhh1')
    cmdPACK.ssh_client = paramiko.SSHClient()

    # Load system host keys and set policy to add missing host keys
    cmdPACK.ssh_client.load_system_host_keys()
    cmdPACK.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cmdPACK.all_configs['pkey'] = get_private_key(cmdPACK.RecordLog,cmdPACK.all_configs['privatekey'])


    ssh_command(
        cmdPACK.RecordLog,
        terminateJOBflag,
        cmdPACK.ssh_client,
        'echo SSH connection established',
        **cmdPACK.all_configs
    )
    print('hhh eenddd')


def stage_cmd_exec(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr, execCMD:str, terminateJOBflag=threading.Event()):
    #additional_cmd = cmdPACK.cmd(execCMD)
    #print('stage_cmd_exec  ', execCMD, cmdPACK.cmd(execCMD))

    ssh_command(
        cmdPACK.RecordLog,
        terminateJOBflag,
        cmdPACK.ssh_client,
        #cmdPACK.cmd(execCMD),
        execCMD,
        **cmdPACK.all_configs
    )

def stage_cmd_run(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    cmd = cmdPACK.cmd('RUN')
    BUG(f'[RunCMD] PyModule {cmdPACK.name} executes cmd "{cmd}"')
    return stage_cmd_exec(cmdPACK,jobSTAT, cmd, terminateJOBflag)
def stage_cmd_test(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    cmd = cmdPACK.cmd('TEST')
    BUG(f'[TestCMD] PyModule {cmdPACK.name} executes test cmd "{cmd}"')
    cmdPACK.RecordLog(f'[TestCMD] PyModule {cmdPACK.name} executes test cmd "{cmd}"')
    return stage_cmd_exec(cmdPACK,jobSTAT, cmd, terminateJOBflag)
def stage_cmd_stop(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    jobSTAT.terminate()
    while True:
        time.sleep(0.5) # waiting for job ended
        if jobSTAT.IsFinished():
            additional_cmd = cmdPACK.cmd('STOP')
            ssh_command(
                cmdPACK.RecordLog,
                terminateJOBflag,
                cmdPACK.ssh_client,
                cmdPACK.cmd('STOP'),
                **cmdPACK.all_configs
            )
            break
def stage_cmd_destroy(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    print('======= destroying -----')
    stage_cmd_stop(cmdPACK, jobSTAT, terminateJOBflag)

    ssh_command(
        cmdPACK.RecordLog,
        terminateJOBflag,
        cmdPACK.ssh_client,
        cmdPACK.cmd('DESTROY'),
        **cmdPACK.all_configs
    )
    cmdPACK.ssh_client.close()
    delattr(cmdPACK, 'ssh_client')
    print('======= destroying ENDDDDD -----')

import StageCMDManager
def StageCMDFactory() -> StageCMDManager.StageCMDMgr:
    def JobStatMgrFactory(jobtype, *args) -> JobStatManager.JobStatMgr:
        class JobStatMgr_BkgJobMonitor(JobStatManager.JobStatMgr_BkgJobMonitor):
            jobtype = 'bkgjobmonitor'
            def __init__(self, newTHREAD, terminateJOB):
                self.thread = newTHREAD
                self.terminate_job = terminateJOB
            def terminate(self):
                self.terminate_job.set()
                self.thread.join() # wait until process finished
            def IsFinished(self):
                return self.thread.is_alive() == False
        class JobStatMgr_SequentialJob(JobStatManager.JobStatMgr_SequentialJob):
            jobtype = 'sequentialjob'
            def __init__(self, newTHREAD, terminateJOB):
                self.thread = newTHREAD
                self.terminate_job = terminateJOB
            def terminate(self):
                self.terminate_job.set()
                self.thread.join() # wait until process finished
            def IsFinished(self):
                return self.thread.is_alive() == False

        if jobtype == 'bkgjobmonitor':
            return JobStatMgr_BkgJobMonitor(*args)
        if jobtype == 'sequentialjob':
            return JobStatMgr_SequentialJob(*args)
        raise NotImplementedError(f'JobStatMgrFactory() : Invalid jobtype "{jobtype}". Check yaml file.')
        # end of jobstatmgrfactory

    class RunCodeAtBkg:
        def __init__(self, execFUNC):
            self.func = execFUNC
        def __call__(self,cmdPACK:JobCMDPackManager.JobCMDPack, prevJOBstat:JobStatManager.JobStatMgr) -> JobStatManager.JobStatMgr:
            terminate_job_flag = threading.Event()
            thread = threading.Thread(target=self.func, args=(cmdPACK,prevJOBstat,terminate_job_flag))
            thread.start()
            return JobStatMgrFactory(cmdPACK.jobtype, thread, terminate_job_flag)


    return StageCMDManager.StageCMDMgr(
                RunCodeAtBkg(stage_cmd_initialize), # Initialize
                RunCodeAtBkg(stage_cmd_run),        # Run
                RunCodeAtBkg(stage_cmd_test),       # Test
                RunCodeAtBkg(stage_cmd_stop),       # Stop
                RunCodeAtBkg(stage_cmd_destroy),    # Destroy
            )


def testfunc():
    log_center = queue.Queue()
    def check_output_of_process(logCENTER):
        idx=0
        monitoring_period = 0.2
        #while not jobstat.IsFinished():
        while True:
            time.sleep(monitoring_period)
            while True:
                try:
                    sys.stdout.write( '[logCENTER] '+logCENTER.get_nowait())
                    #sys.stdout.write(f'[logCENTER]    and is able to accept new job ? {thread_mgr.AbleToAcceptNewJob()}\n')
                except queue.Empty:
                    sys.stdout.flush()
                    #idx+=1
                    if idx==30:
                        print(f'stopping task {idx}')
                        jobstat.terminate()
                        print('job stopped')
                    break
    mesg_center = threading.Thread(target=check_output_of_process, args=(log_center,))
    mesg_center.start()



    cmdpack = JobCMDPackFactory(log_center, 'data/hexactrl_config_sshconn_sequentialjob.yaml')

    jobqueue = queue.Queue()
    stagecmd = StageCMDFactory()
    jobqueue.put(stagecmd.Initialize)
    stagecmd.Configure(cmdpack, firmware='turnOn_FW_V3.sh')
    jobqueue.put(stagecmd.Test)
    jobqueue.put(stagecmd.Destroy)

    jobstat = None
    while jobqueue.qsize()>0:
        print('a10')
        time.sleep(0.5)
        if jobstat != None and not jobstat.IsFinished(): continue

        time.sleep(1.0)
        job = jobqueue.get()
        jobstat = job(cmdpack,jobstat)

    # jobstat = None
    # jobstat = stagecmd.Initialize(cmdpack, jobstat)
    # jobstat = stagecmd.Configure(cmdpack, val='2217')
    # jobstat = stagecmd.Test(cmdpack, jobstat)





    mesg_center.join()
    exit(1)
def mainfunc():
    pass
def DirectlyExecution():
    terminate_job = threading.Event()
    ssh_command(LOG, 'echo STARTING; for a in 1 2 3 4 5 6 ; do echo looping $a; sleep 3; done ; echo ENDING', terminate_job,
        hostname='ntugrid8.phys.ntu.edu.tw', port=22, username='ltsai', privatekey='/Users/noises/.ssh/toNTU8')



if __name__ == "__main__":
    testfunc()
    mainfunc()
    #DirectlyExecution()
