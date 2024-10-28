#!/usr/bin/env python3
import CommandUnits
import subprocess
import multiprocessing


def InitializeCMDParPool() -> dict:
    a = {}
    name = 'test'
    conf = 'test.yaml'
    a[name] = CommandUnits.CMDParameterTest(name,conf)

    return a

def CMDRun(cmdPARdrawer:dict):
    CMD = 'RUN'

    cmd_par = cmdPARdrawer['test']
    getjobinfo = lambda cmdPAR: (CommandUnits.GetJobType(cmdPAR,CMD),CommandUnits.GetBashCommand(cmdPAR,CMD))
    job_type, bash_cmd = getjobinfo(cmd_par)

    cmd_exec(job_type,bash_cmd)
    #cmd_exec(job_type,bash_cmd)
    #if jobtype == 'destroy job':
    #    if hasattr(cmd_par,'process'):
    #        
    #    
    #if jobtype == 'normal':
    #    
    #if jobtype == 'background monitor':

def cmd_exec(jobTYPE, bashCMD):
    try:
        # Run the Python script in the shell and capture its output
        #process = subprocess.Popen(bashCMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        process = subprocess.Popen('sh sshconnect.sh "echo {hexa_controller_address} ; sleep 5; echo {user}"', stdout=subprocess.PIPE, stderr=subprocess.STDOUT,  shell=True)
        #process = subprocess.Popen(['python', 'bb.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        output = stdout.decode() + stderr.decode()
    except Exception as e:
        output = str(e)
    print('aa')
    print(output)
    print('bb')
    return output
        
if __name__ == "__main__":
    modules = InitializeCMDParPool()
    CMDRun(modules)
    #modules['test'].exec()
    import time
    time.sleep(5)

