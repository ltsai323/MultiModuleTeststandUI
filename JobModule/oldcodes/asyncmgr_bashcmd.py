import asyncio
import weakref
import logging
from asyncmgr_base import AsyncManager

class AsyncBashManager(AsyncManager):
    async def _run_bash_cmd(self, cmd):
        return await asyncio.create_subprocess_shell( cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    async def _read_output(self):
        """Reads and prints the output from the running process."""
        if not self.process or self.process.stdout is None: return

        while True:
            if not self.process: break
            if not self.process.stdout: break
            if self.process.stdout.at_eof(): break

            line = await self.process.stdout.readline()
            if line:
                self.log.info(line.decode().strip())
        self.process = None

    def __init__(self, 
                 logOUT, logERR,
                 configs:dict, constCONFIGs:dict,
                 cmdINIT:str, cmdDESTROY:str, cmdRUN:str, cmdSTOP:str,
                 ):
        
        cmdTEMPLATEs = {
                'initialize': cmdINIT,
                'destroy'   : cmdDESTROY,
                'run'       : cmdRUN,
                'stop'      : cmdSTOP
        }
        super(AsyncBashManager, self).__init__(
                logOUT,logERR,
                cmdTEMPLATEs, configs, constCONFIGs,
                )


        self.process = None
        self.task = None

    async def Initialize(self):
        if self.process and self.process.returncode is None:
            self.log.warnging("process is already running... skip new command")
            return
        self.log.debug('[Initialize] Executing CMD')
        command = self.get_full_command_from_cmd_template('initialize')
        if not command: return
        self.process = await self._run_bash_cmd(command)

        # Read output asynchronously
        self.task = asyncio.create_task(self._read_output())

        self.log.debug('[Initialize] Executing CMD SUBMITTED')
    def Destroy(self):
        return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._terminate_code())
        except RuntimeError:
            self.log.info('[NoEventLoop] So skip the further checking...')
            return
        #asyncio.run(self._terminate_code())
        #await self._terminate_code()
        # Run destroy command
        self.log.debug("Executing destroy command...")

        command = self.get_full_command_from_cmd_template('destroy')
        #@if command:
        #@    self.log.debug("Executing destroy command... running")
        #@    self.process = await self._run_bash_cmd(command)
        #@    await self._read_output()
        #@print(f'[PROCESS SHOULD BE None] {self.process}')
        #@self.process = None
        #@self.log.debug("Executing destroy command... FINISHED")
    '''
    async def Destroy(self):
        await self._terminate_code()
        # Run destroy command
        self.log.debug("Executing destroy command...")

        command = self.get_full_command_from_cmd_template('destroy')
        if command:
            self.log.debug("Executing destroy command... running")
            self.process = await self._run_bash_cmd(command)
            await self._read_output()
        print(f'[PROCESS SHOULD BE None] {self.process}')
        self.process = None
        self.log.debug("Executing destroy command... FINISHED")
    '''



    async def Run(self):
        """Starts the bash command asynchronously."""
        if self.process and self.process.returncode is None:
            self.log.warning("Process is already running... skip new command")
            return

        self.log.debug("Starting process...")
        command = self.get_full_command_from_cmd_template('run')
        if not command: return

        self.process = await self._run_bash_cmd(command)
        self.task = asyncio.create_task(self._read_output())

    async def Await(self):
        if  self.process and self.process.returncode is None:
            self.log.debug('[Await] waiting for job finished')
            await self.process.wait()
        if self.task and not self.task.done():
            self.log.debug('[Await] waiting for mesg job finished')
            await self.task



    async def _terminate_code(self):
        """Stops the running process and executes a standalone bash command."""
        self.log.debug("Stop() start")
        '''
        await self._stop_bash_cmd()
        await self._stop_read_output()
        '''
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            self.log.info('[NoEventLoop] So skip the further checking...')
            return

        if not self.process:
            self.log.debug("[Stop] No process running.")
            return

        if self.process.returncode is not None:
            self.log.debug("[Stop] Process already finished.")
        else:
            self.log.debug("[Stop] Terminating process...")
            self.process.terminate()
            await self.process.wait()  # Ensure process stops
            self.log.debug("[Stop] Terminating process... FINISHED")
        if self.task and not self.task.done():
            self.log.debug("[INFO] task is still running. Cancelling now...")
            self.task.cancel()
            try:
                await self.task  # Ensure it's cancelled properly
            except asyncio.CancelledError:
                self.log.debug("[INFO] task was successfully cancelled.")


    async def Stop(self):
        await self._terminate_code()
        # Run stop command
        self.log.debug("Executing stop command...")

        command = self.get_full_command_from_cmd_template('stop')
        if command:
            self.log.debug("Executing stop command... running")
            self.process = await self._run_bash_cmd(command)
            await self._read_output()
        self.process = None
        self.log.debug("Executing stop command... FINISHED")



# ----------------------
# Example Usage
# ----------------------

async def main():
    tmplog = logging.getLogger(__name__)
    # Create multiple instances
    the_config = { 'cmdINIT': 'echo hi ; sleep 1', 'cmdDESTROY': 'echo theDESTROYED', 'cmdRUN': 'for a in {1..10};do echo a ; sleep 0.3; done', 'cmdSTOP': 'echo theSTOP ; sleep 2 ; echo theSTOP ENDED', 'logOUT':tmplog, 'logERR':tmplog, 'configs':{}, 'constCONFIGs':{}}
    instance1 = AsyncBashManager(**the_config)
    the_config = { 'cmdINIT': 'echo hi', 'cmdDESTROY': 'echo theDESTROYED', 'cmdRUN': 'for a in {{1..10}};do echo b ; sleep 0.3; done', 'cmdSTOP': 'echo theSTOP ; sleep 2 ; echo theSTOP ENDED', 'logOUT':tmplog, 'logERR':tmplog, 'configs':{}, 'constCONFIGs':{}}
    instance2 = AsyncBashManager(**the_config)
    the_config = { 'cmdINIT': 'echo hi', 'cmdDESTROY': 'echo theDESTROYED', 'cmdRUN': 'for a in {{1..10}};do echo c ; sleep 0.3; done', 'cmdSTOP': 'echo theSTOP ; sleep 2 ; echo theSTOP ENDED', 'logOUT':tmplog, 'logERR':tmplog, 'configs':{}, 'constCONFIGs':{}}
    instance3 = AsyncBashManager(**the_config)
    instance1.show_all_configurations()

    # Start all instances
    await instance1.Initialize()
    #await asyncio.sleep(0.5)


    await instance1.Run()
    await instance2.Run()
    await instance3.Run()

    # Wait a few seconds
    await asyncio.sleep(2)

    # Stop and delete instance1, ensuring instance2 and instance3 continue
    await instance1.Stop()
    del instance1  # Ensure instance1 is deleted
    instance1 = AsyncBashManager(**the_config)
    print('instance1 is deleted!!!!')

    print("Instance1 stopped, others continue running...")

    # Wait to see output from instance2 and instance3
    #await asyncio.sleep(5)

def testfunc_pack_AsyncBashManager():
    logger = logging.getLogger(__name__)
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



    job = AsyncBashManager(
            logOUT = logger, logERR = logger,
            configs = {}, constCONFIGs = {},
            cmdINIT = cmd_template['init'],
            cmdDESTROY = cmd_template['del'],
            cmdRUN = cmd_template['run'],
            cmdSTOP = cmd_template['stop'],
        )

    print('\n\n>>>>>>>>>>>\nA INITIALIZE <<<<<<<<<<\n\n')
    #asyncio.run(job.Initialize())
    async def IIIINIT(j):
        await j.Initialize()
        await j.Await()
    asyncio.run(IIIINIT(job))
    print('\n\n>>>>>>>>>>>\nA RUN        <<<<<<<<<<\n\n')
    async def RUNNN(j): ### handling the async looping
        await j.Run()

        await asyncio.sleep(2)
        await j.Stop()
        await j.Await()
    asyncio.run(RUNNN(job))
    print('\n\n>>>>>>>>>>>\nA STOP       <<<<<<<<<<\n\n')
    asyncio.run(job.Stop())
    print('\n\n>>>>>>>>>>>\nA DEL        <<<<<<<<<<\n\n')
    job.Destroy()
    del job
    job = 3
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    #asyncio.run(main())  # Run the async event loop
    testfunc_pack_AsyncBashManager()
    #print("KKKKKLSKJDFLKSJDLKFJ")

