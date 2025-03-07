import asyncio
from PythonTools.MyLogging_BashJob1 import log
from PythonTools.MyLogging_BashJob1 import log as bashlog

async def _run_bash_cmd(cmd):
    return await asyncio.create_subprocess_shell( cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
async def _read_output(tag,process):
    """Reads and prints the output from the running process."""
    if not process or process.stdout is None: return

    while True:
        if not process: break
        if not process.stdout: break
        if process.stdout.at_eof(): break

        line = await process.stdout.readline()
        if line:
            bashlog.info(f'[{tag}] {line.decode().strip()}')

class BashJob:
    def __init__(self, tag, bashPROC, mesgTASK):
        self.process = bashPROC
        self.task = mesgTASK
        self.tag = tag
    async def Await(self):
        ''' use "await thisOBJ.Await()" to waiting for the ended '''
        if  self.process and self.process.returncode is None:
            bashlog.debug(f'[{self.tag} - Await] waiting for job finished')
            await self.process.wait()
        if self.task and not self.task.done():
            bashlog.debug(f'[{self.tag} - Await] waiting for mesg job finished')
            await self.task
async def bashcmd(tag, cmd):
    process = await _run_bash_cmd(cmd)
    task = asyncio.create_task(_read_output(tag,process))
    return BashJob(tag, process, task)

if __name__ == "__main__":
    async def aa():
        bb = await bashcmd('test', "for a in {1..100}; do echo aa; sleep 0.5;done")
        await bb.Await()
        

    asyncio.run(aa())
