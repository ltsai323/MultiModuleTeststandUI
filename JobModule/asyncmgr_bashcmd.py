import asyncio
import weakref
import logging
from asyncmgr import AsyncManager

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
                 cmdINIT:str, cmdDESTROY:str, cmdRUN:str, cmdSTOP:str,
                 log):
        super(AsyncBashManager, self).__init__()
        self.commands = {
                'initialize': cmdINIT,
                'destroy'   : cmdDESTROY,
                'run'       : cmdRUN,
                'stop'      : cmdSTOP,
        }

        self.log = log

        self.process = None
        self.task = None

    async def Initialize(self):
        if self.process and self.process.returncode is None:
            self.log.warnging("process is already running... skip new command")
            return
        self.log.debug('[Initialize] Executing CMD')
        command = self.commands['initialize']
        if not command: return
        self.process = await self._run_bash_cmd(command)

        # Read output asynchronously
        self.task = asyncio.create_task(self._read_output())

        self.log.debug('[Initialize] Executing CMD SUBMITTED')
    async def Destroy(self):
        await self._terminate_code()
        # Run destroy command
        self.log.debug("Executing destroy command...")

        command = self.commands['destroy']
        if command:
            self.log.debug("Executing destroy command... running")
            self.process = await self._run_bash_cmd(command)
            await self._read_output()
        print(f'[PROCESS SHOULD BE None] {self.process}')
        self.process = None
        self.log.debug("Executing destroy command... FINISHED")


    def Configure(self):
        pass

    async def Run(self):
        """Starts the bash command asynchronously."""
        if self.process and self.process.returncode is None:
            self.log.warning("Process is already running... skip new command")
            return

        self.log.debug("Starting process...")
        command = self.commands['run']
        if not command: return

        self.process = await self._run_bash_cmd(command)
        self.task = asyncio.create_task(self._read_output())




    async def _terminate_code(self):
        """Stops the running process and executes a standalone bash command."""
        self.log.debug("Stop() start")
        '''
        await self._stop_bash_cmd()
        await self._stop_read_output()
        '''
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

        command = self.commands['stop']
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
    the_config = { 'cmdINIT': 'echo hi ; sleep 1', 'cmdDESTROY': 'echo theDESTROYED', 'cmdRUN': 'for a in {1..10};do echo a ; sleep 0.3; done', 'cmdSTOP': 'echo theSTOP ; sleep 2 ; echo theSTOP ENDED', 'log':tmplog}
    instance1 = AsyncBashManager(**the_config)
    the_config = { 'cmdINIT': 'echo hi', 'cmdDESTROY': 'echo theDESTROYED', 'cmdRUN': 'for a in {1..10};do echo b ; sleep 0.3; done', 'cmdSTOP': 'echo theSTOP ; sleep 2 ; echo theSTOP ENDED', 'log':tmplog}
    instance2 = AsyncBashManager(**the_config)
    the_config = { 'cmdINIT': 'echo hi', 'cmdDESTROY': 'echo theDESTROYED', 'cmdRUN': 'for a in {1..10};do echo c ; sleep 0.3; done', 'cmdSTOP': 'echo theSTOP ; sleep 2 ; echo theSTOP ENDED', 'log':tmplog}
    instance3 = AsyncBashManager(**the_config)

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
    await asyncio.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())  # Run the async event loop

