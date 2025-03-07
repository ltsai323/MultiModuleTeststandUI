import asyncio
from PythonTools.MyLogging_BashJob1 import log as rs232log
from PythonTools.MyLogging_BashJob1 import log as bashlog

import pyvisa


async def set_status(instr, commands):
    ''' set the status. Such as no any read() required. '''
    try:
        for cmd in commands:
            instr.write(cmd)
            
        await asyncio.sleep(0.5)  # Wait 1 second before sending again

    except pyvisa.VisaIOError as e:
        print(f"VISA error: {e}")
    except Exception as e:
        print(f"Error: {e}")
async def IVMonitor(instr,cmds):
    try:
        while True:
            command = "MEAS:CURR?"  # Send command get current
            instr.write(cmds["I"])  # Send command
            meas_I = instr.read().strip()  # Read response

            instr.write(cmds["V"])  # Send command get voltage
            meas_V = instr.read().strip()  # Read response
            
            print(f'[MeasuredIV] V({meas_V}) and I({meas_I})')

            await asyncio.sleep(2)  # Wait 1 second before sending again

    except pyvisa.VisaIOError as e:
        print(f"VISA error: {e}")
    except Exception as e:
        print(f"Error: {e}")


# Run the async function
#asyncio.run(send_command())

class RS232Dev:
    def __init__(self, tag):
        self.rm = pyvisa.ResourceManager()
        self.tag = tag
    def __del__(self):
        self.rm.close()
    def SetTask(self, t):
        self.task = t
    async def Await(self):
        if not hasattr(self, 'task'): return # no task need to wait
        ''' use "await thisOBJ.Await()" to waiting for the ended '''
        if self.task and not self.task.done():
            bashlog.debug(f'[{self.tag} - Await] waiting for mesg job finished')
            await self.task

async def SetPowerStat_GWINSTEK_GPP3323(tag, resource, cmd):
    ''' this is a serial function '''
    commands = {
        'poweron': [
            'VSET1:1.5', # set maximum voltage to 1.5V
            'VSET2:1.5',
            'ISET1:1.0', # set maximum current to 1.0A
            'ISET2:1.0',
            'LOAD1:CV',  # control mode CV
            'LOAD2:CV',
            'OUTPUT1:STATE ON', # power on
            'OUTPUT2:STATE ON', # power on
            ],
        'poweroff': [
            'OUTPUT1:STATE OFF', # power off
            'OUTPUT2:STATE OFF', # power off
            ]
    }
    try:
        cmds = commands[cmd]
    except KeyError as e:
        raise KeyError(f'[Invalid Key] input key "{ cmd }" is not available in "{ commands.keys() }"') from e

    rs232 = RS232Dev(tag)
    instr = rs232.rm.open_resource(resource)
    # Set baud rate and other parameters if needed
    instr.baud_rate = 9600
    instr.timeout = 2000  # 2 seconds timeout

    await set_status(instr, cmds) # waiting for the end
    return rs232
async def IVMonitor_GWINSTEK_GPP3323(tag, resource, cmd):
    ''' this is a bkg running function. This function never neded '''
    rs232 = RS232Dev(tag)
    instr = rs232.rm.open_resource(resource)
    # Set baud rate and other parameters if needed
    instr.baud_rate = 9600
    instr.timeout = 2000  # 2 seconds timeout

    cmds = { 'I': 'MEAS:CURR?', 'V': 'MEAS:VOLT?' }
    task = asyncio.create_task(IVMonitor(instr, cmds))
    rs232.SetTask(task)

    return rs232


    



if __name__ == "__main__":
    DEVICE_ADDRESS = "ASRL/dev/ttyUSB0::INSTR"
    async def ff():
         bbb = await IVMonitor_GWINSTEK_GPP3323('hhh', DEVICE_ADDRESS, '')
         await bbb.Await()
         return
         t = asyncio.create_task(IVMonitor_GWINSTEK_GPP3323('hhh', DEVICE_ADDRESS, '') )
         await t.Await()

    #asyncio.run( ff() )

    #asyncio.run( SetPowerStat_GWINSTEK_GPP3323('hhh', DEVICE_ADDRESS, 'poweron') )
    asyncio.run( SetPowerStat_GWINSTEK_GPP3323('hhh', DEVICE_ADDRESS, 'poweroff') )
