import sys
import threading
import JobCMDPackManager
import queue
import time
import ConfigHandler
import JobStatManager

import pyvisa
import codecs
from dataclasses import dataclass
from DebugManager import BUG

MONITOR_DURATION = 1.0 # second


debug_mode = True
def LOG(mesg:str):
    sys.stdout.write(mesg+'\n')
    sys.stdout.flush()



import re
def complex_cmd_interpreter(s):
    ''' complexCMD like "[jobtype - mesg]cmd" '''
    match = re.match(r"\[(.*)\](.*)", s.strip())

    if '|' in s:
        raise IOError(f'[InvalidFormat] complex_cmd_interpreter() found "|" in complexCMD "{s}" forbidding the matching procedure')
    if match:
        bbb = match.group(1)
        jobtype = bbb.split('-')[0].strip()
        mesg    = bbb.split('-')[1].strip()
        #jobtype = match.group(1)
        cmd = match.group(2)
        return jobtype, mesg, cmd
    else:
        raise ValueError(f'[IncorrectFormat] complex_cmd_interpreter() has weird input "{s}"')


class complex_cmd_donothing:
    identifier = 'donothing'
    def __init__(self, cmd:str, mesg:str):
        self.cmd = cmd
        self.mesg = mesg
    def __str__(self):
        return f'complex_cmd_donothing(cmd={self.cmd}, mesg={self.mesg})'
    def exec(self, rs232INSTANCE, logFUNC, terminateJOB:threading.Event, bkgMONITOR:threading.Event):
        logFUNC(f'[{self.mesg}]')
class complex_cmd_sendcmd:
    identifier = 'sendcmd'
    def __init__(self, cmd:str, mesg:str):
        self.cmd = cmd
        self.mesg = mesg
    def __str__(self):
        return f'complex_cmd_sendcmd(cmd={self.cmd}, mesg={self.mesg})'
    def exec(self, rs232INSTANCE, logFUNC, terminateJOB:threading.Event, bkgMONITOR:threading.Event):
        rs232INSTANCE.write(self.cmd)
        if terminateJOB.is_set(): return
        logFUNC(f'[{self.mesg}]')
class complex_cmd_sendandread:
    identifier = 'sendandread'
    def __init__(self, cmd:str):
        self.cmd = cmd
        self.mesg = mesg
    def __str__(self):
        return f'complex_cmd_sendandread(cmd={self.cmd}, mesg={self.mesg})'
    def exec(self, rs232INSTANCE, logFUNC, terminateJOB:threading.Event, bkgMONITOR:threading.Event):
        rs232INSTANCE.write(self.cmd)
        if terminateJOB.is_set(): return
        logFUNC(f'[{self.mesg}] {rs232INSTANCE.read()}')
class complex_cmd_monitor:
    identifier = 'monitor'
    def __init__(self, cmd:str, mesg:str):
        self.cmd = cmd
        self.mesg = mesg
    def __str__(self):
        return f'complex_cmd_monitor(cmd={self.cmd}, mesg={self.mesg})'
    def exec(self, rs232INSTANCE, logFUNC, terminateJOB:threading.Event, bkgMONITOR:threading.Event):
        bkgMONITOR.set()
        while True:
            rs232INSTANCE.write(self.cmd)
            logFUNC(f'[{self.mesg}] {rs232INSTANCE.read()}')

            time.sleep(MONITOR_DURATION)
            if terminateJOB.is_set():
                break

def complex_cmd_factory(complexCMD:str):
    ''' complexCMD like "[jobtype - mesg]cmd" '''
    jobtype, mesg, cmd = complex_cmd_interpreter(complexCMD)
    if jobtype == complex_cmd_sendcmd.identifier:
        return complex_cmd_sendcmd(cmd,mesg)
    if jobtype == complex_cmd_sendandread.identifier:
        return complex_cmd_sendandread(cmd,mesg)
    if jobtype == complex_cmd_monitor.identifier:
        return complex_cmd_monitor(cmd,mesg)
    if jobtype == complex_cmd_donothing.identifier:
        return complex_cmd_donothing(cmd,mesg)
    raise NotImplementedError(f'[InvalidIdentifier] complex_cmd_factory() : jobtype "{jobtype}" is invalid in complex string "{complexCMD}"')







### main function
def send_rs232_mesg(
        resourceMANAGER:pyvisa.ResourceManager,
        logFUNC,
        resourceSTR:str,
        terminateJOB:threading.Event,
        bkgMONITOR:threading.Event,
        complexCMDs:str):
    rm = resourceMANAGER
    try:
        rs232_instance = rm.open_resource(resourceSTR)
        ## need to handle timeout exception
        rs232_instance.timeout = 200 # 0.2 second timeout
        for complexCMD in complexCMDs.split('|'):
            cCMD = complex_cmd_factory(complexCMD)
            cCMD.exec(rs232_instance,logFUNC,terminateJOB,bkgMONITOR)

    except pyvisa.VisaIOError as e:
        logFUNC('HWConnectError', f'pyvisa reports error : {type(e)} - {e}')
    finally:
        rs232_instance.close()
### main function ended


### Input configurations
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




def JobCMDPackFactory(logQUEUE, yamlFILE:str) -> JobCMDPack:
    from tools.YamlHandler import YamlLoader
    loaded_configs = YamlLoader(yamlFILE)
    cmdTEMPLATE = loaded_configs.configs
    name = loaded_configs.configs['name']
    jobtype = loaded_configs.configs['jobtype']

    parameters = ConfigHandler.LoadedParameterFactory(loaded_configs)
    allconfigs = ConfigHandler.LoadedConfigFactory(loaded_configs)
    commandset = ConfigHandler.LoadedCMDFactory(loaded_configs)

    return JobCMDPack(name,jobtype,logQUEUE,
        commandset, parameters, allconfigs)
### Input configurations ended

### StagedCMD : For Initialize / Configure / Run / Stop / Destroy
def stage_cmd_initialize(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr, terminateJOBflag=threading.Event(), bkgMONITOR=threading.Event()):
    if not hasattr(cmdPACK, 'run_rm'):
        cmdPACK.run_rm = pyvisa.ResourceManager()


    runcmd = cmdPACK.command_set.GetCMD('INITIALIZE', cmdPACK.all_configs) # only INITIALIZE uses  "configs" in yaml file
    BUG(f'Executing CMD: {runcmd}')
    send_rs232_mesg(
            cmdPACK.run_rm,
            cmdPACK.RecordLog,
            cmdPACK.all_configs['resource'],
            terminateJOBflag,bkgMONITOR, runcmd)
    BUG(f'End of CMD: {runcmd}')

def stage_cmd_exec(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr, execCMD:str, terminateJOBflag=threading.Event(), bkgMONITOR=threading.Event()):
    additional_cmd = cmdPACK.cmd(execCMD)
    send_rs232_mesg(
        cmdPACK.run_rm,
        cmdPACK.RecordLog,
        cmdPACK.all_configs['resource'],
        terminateJOBflag,bkgMONITOR, additional_cmd)
def stage_cmd_run(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event(), bkgMONITOR=threading.Event()):
    return stage_cmd_exec(cmdPACK,jobSTAT, 'RUN', terminateJOBflag, bkgMONITOR)
def stage_cmd_test(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event(), bkgMONITOR=threading.Event()):
    return stage_cmd_exec(cmdPACK,jobSTAT, 'TEST', terminateJOBflag, bkgMONITOR)
def stage_cmd_stop(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event(), bkgMONITOR=threading.Event()):
    jobSTAT.terminate()
    while True:
        time.sleep(0.5)
        if jobSTAT.IsFinished():
            additional_cmd = cmdPACK.cmd('STOP')
            send_rs232_mesg(
                cmdPACK.run_rm,
                cmdPACK.RecordLog,
                cmdPACK.all_configs['resource'],
                terminateJOBflag,bkgMONITOR, additional_cmd)
            break
def stage_cmd_destroy(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event(), bkgMONITOR=threading.Event()):
    stage_cmd_stop(cmdPACK, jobSTAT, terminateJOBflag)

    additional_cmd = cmdPACK.cmd('DESTROY')
    send_rs232_mesg(
        cmdPACK.run_rm,
        cmdPACK.RecordLog,
        cmdPACK.all_configs['resource'],
        terminateJOBflag,bkgMONITOR, additional_cmd)
    #cmdPACK.run_rm.close()
    #delattr(cmdPACK, 'run_rm')



import StageCMDManager
def StageCMDFactory() -> StageCMDManager.StageCMDMgr:
    class JobStatMgr(JobStatManager.JobStatMgr):
        def __init__(self, jobTHREAD, terminateJOB, bkgMONITOR):
            self.thread = jobTHREAD
            self.terminate_job = terminateJOB
            self.bkgmonitor = bkgMONITOR
        def terminate(self):
            self.terminate_job.set()
        def IsFinished(self):
            return self.thread.is_alive() == False
        def AbleToAcceptNewJob(self):
            return self.thread.is_alive() == False or self.bkgmonitor.is_set()

    class RunCodeAtBkg:
        def __init__(self, execFUNC):
            self.func = execFUNC
        def __call__(self,cmdPACK:JobCMDPackManager.JobCMDPack, prevJOBstat:JobStatManager.JobStatMgr) -> JobStatManager.JobStatMgr:
            bkg_monitor_flag = threading.Event()
            terminate_job_flag = threading.Event()
            thread = threading.Thread(target=self.func, args=(cmdPACK,prevJOBstat,terminate_job_flag, bkg_monitor_flag))
            thread.start()
            return JobStatMgr(thread, terminate_job_flag, bkg_monitor_flag)

    return StageCMDManager.StageCMDMgr(
                RunCodeAtBkg(stage_cmd_initialize), # Initialize
                RunCodeAtBkg(stage_cmd_run),        # Run
                RunCodeAtBkg(stage_cmd_test),       # Test
                RunCodeAtBkg(stage_cmd_stop),       # Stop
                RunCodeAtBkg(stage_cmd_destroy),    # Destroy
            )
### StagedCMD ended


def mainfunc():
    log_center = queue.Queue()
    cmdpack = JobCMDPackFactory(log_center, 'data/powersupplyUpper_config_rs232cmder.yaml')
    #cmdpack = JobCMDPackFactory(log_center, 'data/config_rs232cmder.yaml')
    stagecmd = StageCMDFactory()


    jobstat = stagecmd.Initialize(cmdpack, None)
    time.sleep(10)
    jobstat = stagecmd.Configure(cmdpack)
    time.sleep(1)
    jobstat = stagecmd.Test(cmdpack, jobstat)
    #jobstat = stagecmd.Run(cmdpack, jobstat)
    #time.sleep(1)

    def check_output_of_process(logCENTER):
        idx=0
        monitoring_period = 0.2
        while not jobstat.IsFinished():
            time.sleep(monitoring_period)
            while True:
                try:
                    sys.stdout.write( '[logCENTER] '+logCENTER.get_nowait()+'\n')
                    #sys.stdout.write(f'[logCENTER]    and is able to accept new job ? {jobstat.AbleToAcceptNewJob()}\n')
                except queue.Empty:
                    sys.stdout.flush()
                    idx+=1
                    if idx==30:
                        print('stopping task')
                        jobstat.terminate()
                        print('job stopped')
                    break
    check_output_of_process(log_center)
    exit()


if __name__ == "__main__":
    mainfunc()
