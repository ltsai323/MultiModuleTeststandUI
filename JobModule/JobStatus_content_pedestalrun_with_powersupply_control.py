import asyncio
import multiprocessing
import os
import signal
import logging
from JobModule.JobStatus_base import JobStatus, JobConf
from JobModule.JobStatus_base import STAT_RUNNING, STAT_BKG_RUN, STAT_FUNCEND, STAT_INVALID
from PythonTools.MyLogging_BashJob1 import log
from PythonTools.MyLogging_BashJob1 import log as bashlog
from JobModule._BashCMD import bashcmd, BashJob
from JobModule.powersupply_GWINSTEK_GPP3323 import IVMonitor_GWINSTEK_GPP3323 as IVMonitor
from JobModule.powersupply_GWINSTEK_GPP3323 import SetPowerStat_GWINSTEK_GPP3323 as SetPowerStat


testmode = False
used_cmds = [
    'init_pwrjob1',  # turn on LV powerU
    'init_bashjob2', # restart i2c-server.service and daq-server.service
    'init_bashjob9', # kria power on && start daq-client

    'run_pwrjob1',  # turn on IV monitoring on LV powerU
    'run_bashjob2', # take data

    'stop_bashjob1', # restart i2c-server.service and daq-server.service

    'destroy_bashjob1',
    'destroy_pwrjob2', # turn off LV powerU
        ]

def init_job(clsCONF, flag):
    async def job_content(clsCONF, flag):
        flag.value = STAT_RUNNING
        if not testmode:
            dev1 = "ASRL/dev/ttyUSB0::INSTR"
            tag,cmd = clsCONF.CMDTag_and_FormattedCMD('init_pwrjob1')
            cmd = 'poweron' # asdf

            if cmd:
                init_pwrjob1 = await SetPowerStat(tag, dev1, cmd)
                await init_pwrjob1.Await()

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('init_bashjob2')
        if cmd:
            bashjob2 = await bashcmd(tag,cmd)
            await bashjob2.Await()



        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('init_bashjob9')
        if cmd:
            log.debug(f'[init_bashjob9] got command "{cmd}"\n\n\n')
            bashjob9 = await bashcmd(tag,cmd)

            flag.value = STAT_BKG_RUN # tag this job should be running in background
            await bashjob9.Await()
            log.debug(f'[init_bashjob9] got command "{cmd}"   EXECTION FINISHED')

        flag.value = STAT_FUNCEND

    asyncio.run(job_content(clsCONF, flag) )


def run_job(clsCONF, flag):
    async def job_content(clsCONF,flag):
        flag.value = STAT_RUNNING

        if not testmode:
            dev1 = "ASRL/dev/ttyUSB0::INSTR"
            tag,cmd = clsCONF.CMDTag_and_FormattedCMD('run_pwrjob1')
            #if cmd: pwrjob1 = asyncio.create_task( IVMonitor(tag, dev1, cmd) )
            if cmd:
                pwrjob1 = await IVMonitor(tag, dev1, cmd)
                ### this is a monitoring job. Not to use await

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('run_bashjob2')
        if cmd:
            bashjob2 = await bashcmd(tag,cmd) # direct run
            await bashjob2.Await()
        #tag,cmd = clsCONF.CMDTag_and_FormattedCMD('run_bashjob9')
        #if cmd: bashjob9 = asyncio.create_task( bashcmd(tag,cmd) )

        # asdf since bashjob2 finished. I should terminate pwrjob1
        flag.value = STAT_FUNCEND # tag this job should be running in background

    asyncio.run( job_content(clsCONF,flag) )

def stop_job(clsCONF, flag):
    async def job_content(clsCONF,flag):
        flag.value = STAT_RUNNING

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('stop_bashjob1')
        if cmd:
            #bashjob1 = asyncio.create_task( bashcmd(tag,cmd) )
            bashjob1 = await bashcmd(tag,cmd)
            await bashjob1.Await()

        flag.value = STAT_FUNCEND # tag this job should be running in background

    asyncio.run( job_content(clsCONF,flag) )


def destroy_job(clsCONF, flag):
    async def job_content(clsCONF,flag):
        flag.value = STAT_RUNNING

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('destroy_bashjob1')
        if cmd:
            #bashjob1 = asyncio.create_task( bashcmd(tag,cmd) )
            bashjob1 = await bashcmd(tag,cmd)
            await bashjob1.Await()
        if not testmode:
            dev1 = "ASRL/dev/ttyUSB0::INSTR"
            tag,cmd = clsCONF.CMDTag_and_FormattedCMD('destroy_pwrjob2')
            cmd = 'poweroff' # asdf
            if cmd: await SetPowerStat(tag, dev1, cmd)

        flag.value = STAT_FUNCEND # tag this job should be running in background

    asyncio.run( job_content(clsCONF,flag) )
