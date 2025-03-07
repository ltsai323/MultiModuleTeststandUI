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
    'init_bashjob1', # restart i2c-server.service and daq-server.service
    'init_pwrjob2',  # turn on LV powerU
    'init_bashjob9', # kria power on && start daq-client

    'run_pwrjob1',  # turn on IV monitoring on LV powerU
    'run_bashjob9', # take data

    'stop_bashjob1', # restart i2c-server.service and daq-server.service

    'destroy_bashjob1',
    'destroy_pwrjob2', # turn off LV powerU
        ]

def init_job(clsCONF, flag):
    async def job_content(clsCONF, flag):
        loop = asyncio.get_running_loop()
        flag.value = STAT_RUNNING
        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('init_bashjob1')
        tasks = []
        if cmd: await bashcmd(tag,cmd)

        if not testmode:
            dev1 = "ASRL/dev/ttyUSB0::INSTR"
            tag,cmd = clsCONF.CMDTag_and_FormattedCMD('init_pwrjob2')
            cmd = 'poweron' # asdf

            if cmd: tasks.append(
                    loop.create_task( SetPowerStat(tag, dev1, cmd) )
                                )

        for task in tasks: await task

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('init_bashjob9')
        if cmd: bashjob9 = loop.create_task( bashcmd(tag,cmd) )

        #await bashjob9.Await()
        flag.value = STAT_BKG_RUN # tag this job should be running in background
        #flag.value = STAT_FUNCEND

    asyncio.run(job_content(clsCONF, flag) )


def run_job(clsCONF, flag):
    async def job_content(clsCONF,flag):
        flag.value = STAT_RUNNING
        loop = asyncio.get_running_loop()

        if not testmode:
            dev1 = "ASRL/dev/ttyUSB0::INSTR"
            tag,cmd = clsCONF.CMDTag_and_FormattedCMD('run_pwrjob1')
            if cmd: pwrjob1 = loop.create_task( IVMonitor(tag, dev1, cmd) )

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('run_bashjob9')
        if cmd: bashjob9 = loop.create_task( bashcmd(tag,cmd) )

        flag.value = STAT_BKG_RUN # tag this job should be running in background

    asyncio.run( job_content(clsCONF,flag) )

def stop_job(clsCONF, flag):
    async def job_content(clsCONF,flag):
        flag.value = STAT_RUNNING

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('stop_bashjob1')
        if cmd:
            bashjob1 = loop.create_task( bashcmd(tag,cmd) )
            await bashjob1

        flag.value = STAT_FUNCEND # tag this job should be running in background

    asyncio.run( job_content(clsCONF,flag) )


def destroy_job(clsCONF, flag):
    async def job_content(clsCONF,flag):
        flag.value = STAT_RUNNING

        tag,cmd = clsCONF.CMDTag_and_FormattedCMD('destroy_bashjob1')
        if cmd:
            bashjob1 = loop.create_task( bashcmd(tag,cmd) )
            await bashjob1
        if not testmode:
            dev1 = "ASRL/dev/ttyUSB0::INSTR"
            tag,cmd = clsCONF.CMDTag_and_FormattedCMD('destroy_pwrjob2')
            cmd = 'poweroff' # asdf
            if cmd: await SetPowerStat(tag, dev1, cmd)

        flag.value = STAT_FUNCEND # tag this job should be running in background

    asyncio.run( job_content(clsCONF,flag) )
