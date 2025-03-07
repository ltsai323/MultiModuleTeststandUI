import asyncio
import multiprocessing
import signal
import logging
from JobModule.JobStatus_base import JobStatus, JobConf
from JobModule.JobStatus_base import STAT_RUNNING, STAT_BKG_RUN, STAT_FUNCEND, STAT_INVALID
from PythonTools.MyLogging_BashJob1 import log
from PythonTools.MyLogging_BashJob1 import log as bashlog
from JobModule._BashCMD import bashcmd, BashJob
#from JobModule.JobStatus_content_example_run2bashcmd import init_job, run_job, stop_job, destroy_job, used_cmds
from JobModule.JobStatus_content_pedestalrun_with_powersupply_control import init_job, run_job, stop_job, destroy_job, used_cmds




def destroy_process(clsOBJ, processNAME):
    if hasattr(clsOBJ, processNAME):
        process = getattr(clsOBJ, processNAME)
        process.terminate()
        process.join()  # Ensure the process stops
        delattr(clsOBJ, processNAME)
def destroy_flag(clsOBJ, flagNAME):
    if hasattr(clsOBJ, flagNAME):
        delattr(clsOBJ, flagNAME)









class JobStatus_Startup(JobStatus):
    status = 'startup'
    def __init__(self, jobCONF:JobConf): # asdfasdfasdf
        super().__init__(None)
        self.bkgjob_init_flag = multiprocessing.Value('i', STAT_INVALID)
        jobCONF.ValidCheck(*used_cmds)
        self.config = jobCONF
    def fetch_current_obj(self):
        if self.bkgjob_init_flag.value <= 0:
            log.debug(f'[StayCurrentObj] Keeps status "{self.status}"')
            return self
        log.debug(f'[NewObj] Move to new object "JobStatus_Initializing". Initializing object from JobStatus_Startup')
        return JobStatus_Initializing(self)
        
    def Initialize(self):
        log.debug(f'[InitializeCMD] Initializing current job from status "{ self.status }"')
        if self.bkgjob_init_flag.value != STAT_INVALID:
            log.warning(f'[Initializing] The job is initializing ... Please use fetch_current_obj() to fetch current object')
            return
        
        #init_job(self.config, self.bkgjob_init_flag)
        self.bkgjob_init_process = multiprocessing.Process(target=init_job, args=(self.config, self.bkgjob_init_flag))
        self.bkgjob_init_process.start()

def testfunc_JobStatus_Startup():
    job = JobStatus_Startup()
    job.Initialize()
    #job.Run()
    input("Put enter to stop all program\n\n")
    print(f'[current status] job.bkgjob_init_flag = {job.bkgjob_init_flag.value}')
    job = job.fetch_current_obj()
    print(job)
    input("Put enter to stop all program\n\n")
    print(f'[current status] job.bkgjob_init_flag = {job.bkgjob_init_flag.value}')
    job = job.fetch_current_obj()
    print(job)
    input("Put enter to stop all program\n\n")
    print(f'[current status] job.bkgjob_init_flag = {job.bkgjob_init_flag.value}')
    job = job.fetch_current_obj()
    print(job)
    job.bkgjob_init_process.terminate()
    job.bkgjob_init_process.join()


class JobStatus_Initializing(JobStatus):
    status = 'initializing'
    def __init__(self, prevSTATobj):
        super().__init__(prevSTATobj)
        if not hasattr(self, 'bkgjob_init_flag'   ): raise RuntimeError('[InvalidObject] JobStatus_Initializing() requires class attribute "bkgjob_init_flag"')
        if not hasattr(self, 'bkgjob_init_process'): raise RuntimeError('[InvalidObject] JobStatus_Initializing() requires class attribute "bkgjob_init_process"')
    def fetch_current_obj(self):
        if not hasattr(self, 'bkgjob_init_flag'):
            log.debug(f'[ObjectDestroyed] Move object to JobStatus_Destroyed')
            return JobStatus_Destroyed(self)

        if self.bkgjob_init_flag.value <= 0:
            log.debug(f'[StayCurrentObj] Keeps status "{self.status}"')
            return self
        log.debug(f'[NewObj] Move to new object "JobStatus_Initialized". Initialize() finished.')
        return JobStatus_Initialized(self)
        
    def Destroy(self):
        log.debug(f'[DestroyCMD] Destroying from status "{ self.status }"')
        destroy_process(self, 'bkgjob_main_process')
        destroy_flag   (self, 'bkgjob_main_flag'   )
        destroy_process(self, 'bkgjob_init_process')
        destroy_flag   (self, 'bkgjob_init_flag'   )

        self.destroy_flag = multiprocessing.Value('i', STAT_INVALID)
        self.destroy_process = multiprocessing.Process(target=destroy_job, args=(self.config, self.destroy_flag))
        self.destroy_process.start()
        self.destroy_process.join()
        delattr(self, 'destroy_flag')
        delattr(self, 'destroy_process')

class JobStatus_Initialized(JobStatus):
    status = 'initialized' # Initialized is equal to Idle
    def __init__(self, prevSTATobj):
        super().__init__(prevSTATobj)
        if not hasattr(self, 'bkgjob_init_flag'   ): raise RuntimeError('[InvalidObject] JobStatus_Initializing() requires class attribute "bkgjob_init_flag"')
        if not hasattr(self, 'bkgjob_init_process'): raise RuntimeError('[InvalidObject] JobStatus_Initializing() requires class attribute "bkgjob_init_process"')
        self.configured = False
    def execute(self):
        pass
    def fetch_current_obj(self):
        if not hasattr(self, 'bkgjob_init_flag'):
            log.debug(f'[ObjectDestroyed] Move object to JobStatus_Destroyed')
            return JobStatus_Destroyed(self)

        if not self.configured:
            log.debug(f'[StayCurrentObj] Keeps status "{self.status}"')
            return self
        delattr(self, 'configured')
        log.debug(f'[NewObj] Move to new object "JobStatus_Configured". Need to use Configure() put runtime information')
        return JobStatus_Configured(self)
        
    def Configure(self, confDICT):
        log.debug(f'[ConfigureCMD] set runtime variable to arguments from status "{ self.status }"')
        self.config.Configure(confDICT)
        self.configured = True

    def Destroy(self):
        log.debug(f'[DestroyCMD] Destroying from status "{ self.status }"')
        destroy_process(self, 'bkgjob_main_process')
        destroy_flag   (self, 'bkgjob_main_flag'   )
        destroy_process(self, 'bkgjob_init_process')
        destroy_flag   (self, 'bkgjob_init_flag'   )

        self.destroy_flag = multiprocessing.Value('i', STAT_INVALID)
        self.destroy_process = multiprocessing.Process(target=destroy_job, args=(self.config, self.destroy_flag))
        self.destroy_process.start()
        self.destroy_process.join()
        delattr(self, 'destroy_flag')
        delattr(self, 'destroy_process')



class JobStatus_Configured(JobStatus):
    status = 'configured'
    def __init__(self, prevSTATobj):
        super().__init__(prevSTATobj)
        self.bkgjob_main_flag = multiprocessing.Value('i', STAT_INVALID)
    def fetch_current_obj(self):
        if not hasattr(self, 'bkgjob_init_flag'):
            log.debug(f'[ObjectDestroyed] Move object to JobStatus_Destroyed')
            return JobStatus_Destroyed(self)

        if self.bkgjob_main_flag.value == STAT_INVALID:
            log.debug(f'[StayCurrentObj] Keeps status "{self.status}"')
            return self
        log.debug(f'[NewObj] Move to new object "JobStatus_Running". run time configuration finished')
        return JobStatus_Running(self)

    def Configure(self, confDICT):
        log.debug(f'[ConfigureCMD] set runtime variable to arguments from status "{ self.status }"')
        self.config.Configure(confDICT)
        return  # JobStatus_Configured would not generate another JobStatus_Configured object
    def Run(self):
        log.debug(f'[RunCMD] Running current job from status "{ self.status }"')
        if self.bkgjob_main_flag.value != STAT_INVALID:
            log.warning(f'[Initializing] The job is initializing ... Please use fetch_current_obj() to fetch current object')
            return
        
        #main_job(self.config, self.bkgjob_main_flag)
        self.bkgjob_main_process = multiprocessing.Process(target=run_job, args=(self.config, self.bkgjob_main_flag))
        self.bkgjob_main_process.start()
        
    def Destroy(self):
        log.debug(f'[DestroyCMD] Destroying from status "{ self.status }"')
        destroy_process(self, 'bkgjob_main_process')
        destroy_flag   (self, 'bkgjob_main_flag'   )
        destroy_process(self, 'bkgjob_init_process')
        destroy_flag   (self, 'bkgjob_init_flag'   )

        self.destroy_flag = multiprocessing.Value('i', STAT_INVALID)
        self.destroy_process = multiprocessing.Process(target=destroy_job, args=(self.config, self.destroy_flag))
        self.destroy_process.start()
        self.destroy_process.join()
        delattr(self, 'destroy_flag')
        delattr(self, 'destroy_process')

class JobStatus_Running(JobStatus):
    status = 'running'
    def __init__(self, prevSTATobj):
        super().__init__(prevSTATobj)
    def fetch_current_obj(self):
        if not hasattr(self, 'bkgjob_init_flag'):
            log.debug(f'[ObjectDestroyed] Move object to JobStatus_Destroyed')
            return JobStatus_Destroyed(self)

        if hasattr(self, 'bkgjob_main_flag') and getattr(self, 'bkgjob_main_flag').value <= 0:
            log.debug(f'[StayCurrentObj] Keeps status "{self.status}"')
            return self

        log.debug(f'[NewObj] Move to new object "JobStatus_Initialized". Job is stopped or finished')
        return JobStatus_Initialized(self)

    def Stop(self):
        log.debug(f'[StopCMD] Stopping current job')
        destroy_process(self, 'bkgjob_main_process')
        destroy_flag   (self, 'bkgjob_main_flag'   )

        self.stop_flag = multiprocessing.Value('i', STAT_INVALID)
        self.stop_process = multiprocessing.Process(target=stop_job, args=(self.config, self.stop_flag))
        self.stop_process.start()
        self.stop_process.join()
        delattr(self, 'stop_flag')
        delattr(self, 'stop_process')

    def Destroy(self):
        log.debug(f'[DestroyCMD] Destroying from status "{ self.status }"')
        destroy_process(self, 'bkgjob_main_process')
        destroy_flag   (self, 'bkgjob_main_flag'   )
        destroy_process(self, 'bkgjob_init_process')
        destroy_flag   (self, 'bkgjob_init_flag'   )

        self.destroy_flag = multiprocessing.Value('i', STAT_INVALID)
        self.destroy_process = multiprocessing.Process(target=destroy_job, args=(self.config, self.destroy_flag))
        self.destroy_process.start()
        self.destroy_process.join()
        delattr(self, 'destroy_flag')
        delattr(self, 'destroy_process')


class JobStatus_Destroyed(JobStatus):
    status = 'destroyed' # the difference between state 'startup' and 'destroyed' is the __init__()
    def __init__(self, prevSTATobj): # asdfasdfasdf
        super().__init__(prevSTATobj)
        self.bkgjob_init_flag = multiprocessing.Value('i', STAT_INVALID)

    def fetch_current_obj(self):
        if self.bkgjob_init_flag.value <= 0:
            log.debug(f'[StayCurrentObj] Keeps status "{self.status}"')
            return self
        log.debug(f'[NewObj] Move to new object "JobStatus_Initializing". Job successfully Destroyed')
        return JobStatus_Initializing(self)
        
    def Initialize(self):
        log.debug(f'[InitializeCMD] Initializing current job from status "{ self.status }"')
        if self.bkgjob_init_flag.value != STAT_INVALID:
            log.warning(f'[Initializing] The job is initializing ... Please use fetch_current_obj() to fetch current object')
            return
        
        #init_job(self.config, self.bkgjob_init_flag)
        self.bkgjob_init_process = multiprocessing.Process(target=init_job, args=(self.config, self.bkgjob_init_flag))
        self.bkgjob_init_process.start()


def testfunc_JobStatus_whole_flow():
    cmd_templates = {
    'init_bashjob1'     : 'echo hi {initVar1}',
    'init_pwrjob2'      : 'poweron',
    'init_bashjob9'     : 'echo hi 999',

    'run_pwrjob1'       : 'kkk',
    'run_bashjob9'      : 'echo jjj {constVar}',

    'stop_bashjob1'     : '',

    'destroy_pwrjob1'   : 'poweroff',
    }
    cmd_arg = {
            'initVar1': 'this is initVar1',
    }
    cmd_const = {
            'constVar': 'this is constant variable',
    }
    jobconf = JobConf(cmd_templates, cmd_arg, cmd_const)
    job = JobStatus_Startup(jobconf)
    job.Initialize()
    input("Put enter to stop all program")
    print(f'[current status] job.bkgjob_init_flag = {job.bkgjob_init_flag.value}')
    job = job.fetch_current_obj()
    while True:
        input("Put enter to stop all program")
        print(f'[current status] job.bkgjob_init_flag = {job.bkgjob_init_flag.value}')
        job = job.fetch_current_obj()
        print(job)
        print('Configure--')
        job.Configure({'aaD':'cc'})
        print('Run--')
        job.Run()
        print('Stop--')
        job.Stop()

    print(job)
    input("Put enter to stop all program")
    print(f'[current status] job.bkgjob_init_flag = {job.bkgjob_init_flag.value}')
    job = job.fetch_current_obj()
    job.Destroy()
    print(job)
    job.bkgjob_init_process.terminate()
    job.bkgjob_init_process.join()

if __name__ == "__main__":
    #testfunc_JobStatus_Startup()
    testfunc_JobStatus_whole_flow()


