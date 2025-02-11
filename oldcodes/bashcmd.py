import argparse
import sys
import threading
import JobCMDPackManager
import queue
import time
import ConfigHandler
import JobStatManager
import subprocess


def LOG(mesg:str):
    sys.stdout.write(mesg+'\n')
    sys.stdout.flush()



### main function
def bash_command(command:str):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1, shell=True)
    return process

def get_output(logFUNC, pipeMESG):
    for line in iter(pipeMESG.readline, b''):
        logFUNC(line.decode().rstrip())


class JobCMDPack(JobCMDPackManager.JobCMDPack):
    def __init__(self, name:str, jobtype:str, logQUEUE,
                 commandSET:ConfigHandler.LoadedCMDFactory,
                 loadedPARs:ConfigHandler.LoadedParameterFactory,
                 allCONFIGs:dict, execFUNC):
        super().__init__(name,jobtype,logQUEUE,loadedPARs)
        self.command_set = commandSET
        self.loaded_pars = loadedPARs
        self.all_configs = allCONFIGs
        self.exec_func = execFUNC
    def cmd(self, stagedCMD):
        return self.command_set.GetCMD(stagedCMD,self.GetParDict())
    def execute(self,cmdPACK, stagedCMD):
        return self.exec_func(cmdPACK,stagedCMD)


def BashCMD_JobStatMgrFactory(jobtype, *args) -> JobStatManager.JobStatMgr:
    class BashCMD_JobStatMgr_BkgJobMonitor(JobStatManager.JobStatMgr_BkgJobMonitor):
        def __init__(self, process, stdoutTHREAD, stderrTHREAD):
            self.proc = process
            self.threadO = stdoutTHREAD
            self.threadE = stderrTHREAD
        def terminate(self):
            self.proc.kill()
        def IsFinished(self):
            return self.proc.poll() is not None

    class BashCMD_JobStatMgr_SequentialJob(JobStatManager.JobStatMgr_SequentialJob):
        def __init__(self, process, stdoutTHREAD, stderrTHREAD):
            self.proc = process
            self.threadO = stdoutTHREAD
            self.threadE = stderrTHREAD
        def terminate(self):
            self.proc.kill()
        def IsFinished(self):
            return self.proc.poll() is not None
    if jobtype == 'bkgjobmonitor':
        return BashCMD_JobStatMgr_BkgJobMonitor(*args)
    if jobtype == 'sequentialjob':
        return BashCMD_JobStatMgr_SequentialJob(*args)
    raise NotImplementedError(f'[InvalidJobType] BashCMD_JobStatMgrFactory() : Invalid jobtype "{jobtype}". Check yaml file.')


def run_code_at_bkg(cmdPACK:JobCMDPackManager.JobCMDPack, stageCMD:str) -> JobStatManager.JobStatMgr:
    proc = bash_command(cmdPACK.cmd(stageCMD))
    threadO = threading.Thread(target=get_output, args=(cmdPACK.RecordLog,proc.stdout))
    threadE = threading.Thread(target=get_output, args=(cmdPACK.RecordErr,proc.stderr))

    threadO.start()
    threadE.start()

    return BashCMD_JobStatMgrFactory(cmdPACK.jobtype,proc,threadO,threadE)


def JobCMDPackFactory(logQUEUE, yamlFILE:str) -> JobCMDPackManager.JobCMDPack:
    from tools.YamlHandler import YamlLoader
    loaded_configs = YamlLoader(yamlFILE)
    cmdTEMPLATE = loaded_configs.configs
    name = loaded_configs.configs['name']
    jobtype = loaded_configs.configs['jobtype']

    parameters = ConfigHandler.LoadedParameterFactory(loaded_configs)
    allconfigs = ConfigHandler.LoadedConfigFactory(loaded_configs)
    commandset = ConfigHandler.LoadedCMDFactory(loaded_configs)

    return JobCMDPack(name, jobtype, logQUEUE,
        commandset, parameters, allconfigs, run_code_at_bkg)




def testfunc():
    log_center = queue.Queue()
    cmdpack = JobCMDPackFactory(log_center, 'data/config_bashcmd_bkgjobmonitor.yaml')
    cmdpack.SetPar('boardtype', 'HD')
    cmdpack.SetPar('boardID', 'asldkfjasldkf')
    thread_mgr = cmdpack.execute(cmdpack, 'TEST')

    def check_output_of_process(logCENTER, threadMGR):
        idx=0
        monitoring_period = 0.2
        while not threadMGR.IsFinished():
            time.sleep(monitoring_period)
            while True:
                try:
                    sys.stdout.write('[logCENTER] '+logCENTER.get_nowait()+'\n')
                except queue.Empty:
                    sys.stdout.flush()
                    #idx+=1
                    #if idx==10:
                    #    print('stopping task')
                    #    thread_mgr.terminate()
                    #    print('job stopped')
                    break
    check_output_of_process(log_center, thread_mgr)
    exit(1)

def mainfunc():
    proc = bash_command('echo aaaaaa && sleep 5 && echo a2 && sleep 5 && echo finished')
    thread = threading.Thread(target=get_output, args=(LOG,proc.stdout))
    thread.start()

    import time
    time.sleep(10)
    print('[after sleep] kill job')
    proc.kill()
    print('[after sleep] job killed')
    thread.join()

    exit()


if __name__ == "__main__":
    testfunc()
    mainfunc()
