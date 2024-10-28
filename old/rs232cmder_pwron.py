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

MONITOR_DURATION = 1.0 # second


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
    def exec(self, rs232INSTANCE, logFUNC, terminateJOB:threading.Event):
        logFUNC(f'[{self.mesg}]')
class complex_cmd_sendcmd:
    identifier = 'sendcmd'
    def __init__(self, cmd:str, mesg:str):
        self.cmd = cmd
        self.mesg = mesg
    def __str__(self):
        return f'complex_cmd_sendcmd(cmd={self.cmd}, mesg={self.mesg})'
    def exec(self, rs232INSTANCE, logFUNC, terminateJOB:threading.Event):
        rs232INSTANCE.write(self.cmd)
        if terminateJOB.is_set(): return
        logFUNC(f'[{self.mesg}]')
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







# block2 main function
def send_rs232_mesg(
        resourceMANAGER:pyvisa.ResourceManager,
        logFUNC,
        resourceSTR:str,
        terminateJOB:threading.Event,
        complexCMDs:str):
    rm = resourceMANAGER
    try:
        rs232_instance = rm.open_resource(resourceSTR)
        ## need to handle timeout exception
        rs232_instance.timeout = 200 # 0.2 second timeout
        for complexCMD in complexCMDs.split('|'):
            cCMD = complex_cmd_factory(complexCMD)
            cCMD.exec(rs232_instance,logFUNC,terminateJOB)

    except pyvisa.VisaIOError as e:
        logFUNC('HWConnectError', f'pyvisa reports error : {type(e)} - {e}')
    finally:
        rs232_instance.close()


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

## Checking the availablity is put at another code. (Init / Destroy)
def stage_cmd_initialize(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr, terminateJOBflag=threading.Event()):
    cmdPACK.run_rm = pyvisa.ResourceManager()

    init_cmd_before_run = [
        '[sendcmd - power on]A'
        ]
    send_rs232_mesg(
            cmdPACK.run_rm,
            cmdPACK.RecordLog,
            cmdPACK.all_configs['resource'],
            terminateJOBflag, '|'.join(init_cmd_before_run))
def stage_cmd_exec(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr, execCMD:str, terminateJOBflag=threading.Event()):
    additional_cmd = cmdPACK.cmd(execCMD)
    send_rs232_mesg(
        cmdPACK.run_rm,
        cmdPACK.RecordLog,
        cmdPACK.all_configs['resource'],
        terminateJOBflag, additional_cmd)
def stage_cmd_run(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    return stage_cmd_exec(cmdPACK,jobSTAT, 'RUN', terminateJOBflag)
def stage_cmd_test(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    return stage_cmd_exec(cmdPACK,jobSTAT, 'TEST', terminateJOBflag)
def stage_cmd_stop(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    jobSTAT.terminate()
    while True:
        time.sleep(0.5)
        if jobSTAT.IsFinished():
            additional_cmd = cmdPACK.cmd('STOP')
            send_rs232_mesg(
                cmdPACK.run_rm,
                cmdPACK.RecordLog,
                cmdPACK.all_configs['resource'],
                terminateJOBflag, additional_cmd)
def stage_cmd_destroy(cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr,terminateJOBflag=threading.Event()):
    stage_cmd_stop(cmdPACK, jobSTAT, terminateJOBflag)

    additional_cmd = cmdPACK.cmd('DESTROY')
    send_rs232_mesg(
        cmdPACK.run_rm,
        cmdPACK.RecordLog,
        cmdPACK.all_configs['resource'],
        terminateJOBflag, additional_cmd)
    cmdPACK.run_rm.close()
    delattr(cmdPACK, 'run_rm')



import StageCMDManager
def StageCMDFactory() -> StageCMDManager.StageCMDMgr:
    class JobStatMgr(JobStatManager.JobStatMgr):
        def __init__(self, jobTHREAD, terminateJOB):
            self.thread = jobTHREAD
            self.terminate_job = terminateJOB
        def terminate(self):
            self.terminate_job.set()
        def IsFinished(self):
            return self.thread.is_alive() == False

    class RunCodeAtBkg:
        def __init__(self, execFUNC):
            self.func = execFUNC
        def __call__(self,cmdPACK:JobCMDPackManager.JobCMDPack, prevJOBstat:JobStatManager.JobStatMgr) -> JobStatManager.JobStatMgr:
            terminate_job_flag = threading.Event()
            thread = threading.Thread(target=self.func, args=(cmdPACK,prevJOBstat,terminate_job_flag))
            thread.start()
            return JobStatMgr(thread, terminate_job_flag)

    return StageCMDManager.StageCMDMgr(
                RunCodeAtBkg(stage_cmd_initialize), # Initialize
                RunCodeAtBkg(stage_cmd_run),        # Run
                RunCodeAtBkg(stage_cmd_test),       # Test
                RunCodeAtBkg(stage_cmd_stop),       # Stop
                RunCodeAtBkg(stage_cmd_destroy),    # Destroy
            )

'''
def __orig_main_func__(theCONFIGs:SocketProtocol.RunningConfigurations,command:MesgHub.CMDUnit):
    print('CMD Received', str(command))

    def send_rs232_mesg(mesg:str):
        if not hasattr(theCONFIGs,'rm'): # rm = pyvisa.ResourceManager()
            print('NotInitializedError', f'pyvisa is not connected to RS232 device. Initialize before send any message')
        try:
            rs232_instance = theCONFIGs.rm.open_resource(theCONFIGs.resource)
            if mesg:
                rs232_instance.write(mesg)
                return 'out mesg from rs232'
        except pyvisa.VisaIOError as e:
            print('HWConnectError', f'pyvisa reports error : {type(e)} - {e}')
        finally:
            rs232_instance.close()
        return 'nothing send to HW'

    mesg_box = ''
    if command.cmd == CMD.CONNECT:
        theCONFIGs.name = command.arg # Set PyModule name
        BUG('current config name is ', theCONFIGs.name)
        theCONFIGs.rm = pyvisa.ResourceManager()
        out_mesg = send_rs232_mesg('')
        mesg_box = f'RS232 Connection checked. out_mesg = {out_mesg}'
    if command.cmd == CMD.ACTIVATE_POWER_SUPPLY:
        out_mesg = send_rs232_mesg(':OUTPUT1:STATE ON')
        mesg_box = f'Power supply activated. Voltage "{out_mesg}" and Current "{out_mesg}"'
    if command.cmd == CMD.DEACTIVATE_POWER_SUPPLY:
        out_mesg = send_rs232_mesg('OUTPUT:STATE OFF')
        mesg_box = f'Power supply disabled.'
    if command.cmd == CMD.SET_CONFIGS:
        out_mesg = send_rs232_mesg(f'VSET1:{theCONFIGs.MaximumOutputVoltage}')
        out_mesg = send_rs232_mesg(f'ISET1:{theCONFIGs.MaximumOutputCurrent}')
        out_mesg = send_rs232_mesg(f'LOAD1:{theCONFIGs.ControlMode}')
        mesg_box = f'Configs synchronized via RS232'

    if command.cmd == CMD.UPDATE_CONFIG:
        'aaa:3.14|bbb:6.28|ccc:7.19'
        theCONFIGs.SetValues(command.arg)
        mesg_box = f'Update configuration command.arg'

    if command.cmd == CMD.DESTROY:
        theCONFIGs.rm.close()
        mesg_box = f'Remove RS232 connection instance.'



    #send_rs232_mesg(LOG, ':OUTPUT1:STATE ON')
    #send_rs232_mesg(LOG, ':OUTPUT1:STATE?') # good. return output status of channel 1
    #send_rs232_mesg(LOG, ':OUTPUT1:OVP:STATE?') # good. But I don't know what is this value meaning
    send_rs232_mesg(LOG, ':MEASURE1:ALL?') # good. Read volt,current,watt separated by comma
    #send_rs232_mesg(LOG, 'VSET1?') # good
    #send_rs232_mesg(LOG, 'ISET1?') # good
    print('JOB_FINISHED', mesg_box)
'''


def testfunc():
    log_center = queue.Queue()
    cmdpack = JobCMDPackFactory(log_center, 'data/config_rs232cmder_pwron.yaml')
    stagecmd = StageCMDFactory()


    jobstat = stagecmd.Initialize(cmdpack, None)
    time.sleep(1)
    jobstat = stagecmd.Configure(cmdpack)
    time.sleep(20)
    jobstat = stagecmd.Test(cmdpack, jobstat)
    time.sleep(1)

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
def mainfunc():
    log_center = queue.Queue()
    #cmdpack = JobCMDPackFactory(log_center, 'data/config_rs232cmder_bkgjobmonitor.yaml')
    cmdpack = JobCMDPackFactory(log_center, 'data/config_rs232cmder_pwron.yaml')
    stagecmd = StageCMDFactory()


    jobstat = stagecmd.Initialize(cmdpack, None)
    time.sleep(1)
    jobstat = stagecmd.Configure(cmdpack)
    #time.sleep(1)
    jobstat = stagecmd.Run(cmdpack, jobstat)
    time.sleep(1)

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
    testfunc()
    #mainfunc()
