import codecs
from dataclasses import dataclass
import tools.SocketProtocol_ as SocketProtocol
import tools.MesgHub as MesgHub
import time

@dataclass
class Configurations:
    name:str

    output_voltage:float
    resource:str


import sys
def LOG(info,name,mesg):
    print(f'[{info} - LOG] ({name}) {mesg}', file=sys.stderr)


def execute_command(socketPROFILE:SocketProtocol.SocketProfile, clientSOCKET,command):
    socketPROFILE.job_is_running.set()
    status_message = f"Command '{command}' executed successfully."
    LOG('Job finished', 'execute_command', f'Sending mesg to client : {status_message}')

    mesg = MesgHub.CMDUnitFactory( name='execute_command', cmd='TESTING', arg=status_message)
    SocketProtocol.UpdateMesgAndSend( socketPROFILE, clientSOCKET, 'RUNNING', status_message)


    time.sleep(5.0)
    socketPROFILE.job_is_running.clear()
    SocketProtocol.UpdateMesgAndSend( socketPROFILE, clientSOCKET, 'JOB_FINISHED')


if __name__ == "__main__":
    connection_profile = SocketProtocol.SocketProfile('selfTester',execute_command)
    SocketProtocol.start_server(connection_profile)
