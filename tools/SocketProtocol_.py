import socket
import threading
import time
import sys
import tools.MesgHub as MesgHub
from tools.LogTool import LOG
import tools.StatusDefinition as Status
import tools.SocketCommands as ConnCMD
MAX_MESG_LENG = 1024
SET_TIMEOUT = 3.0 # only used for connection checking and system cmd

'''
Need to handle multiple messages problem.
Sometimes socket stocked by multiple messages like [> mesg1 <][> mesg2 <].
'''


def LOG(info,name,mesg):
    print(f'[{info} - LOG] (SocketProtocol-{name}) {mesg}', file=sys.stderr)

MODULE_STATUS = {
        'NOT_INITIALIZED': -2,

        'ERR': -1,
        'idle': 0,
        'monitor': 1, # send readout value periodically
        'running': 2, # send message immediately
        }
class RunningConfigurations:
    def __init__(self, logFUNC = print ):
        self.status = 0
        self.name = 'NotInitialized'
        self.logFUNC = print

        self.module_status = MODULE_STATUS['idle']
    def LOG(self, stat, mesg):
        self.logFUNC(stat,mesg)

    def SetDefault(self, loadedCONFIGs):
        for key,val in loadedCONFIGs.configs.items():
            setattr(self,key,val)
        self.default_configs = loadedCONFIGs.configs
    def SetValue(self, key,val):
        if key == 'runCMD': return # not to update runCMD
        if hasattr(self,key):
            setattr(self, key,val)
            LOG('Config Updated!', 'SetValue()', f'config "{key}" is set to "{val}" now')
        else:
            raise IOError(f'RunningConfigurations::SetValue() : input value "{key}" does not exist. Available keys are {self.default_configs.keys()}')
    def SetValues(self, argSTR):
        update_list = argSTR.split('|')
        for update_item in update_list:
            if update_item == '': continue
            name,val = update_item.split(':')
            self.SetValue(name,val)
class SocketProfile:
    def __init__(self, mainFUNC, runCONFIGs:RunningConfigurations):
        self.mainfunc = mainFUNC
        self.server_socket_is_active = threading.Event()
        self.client_socket_is_active = threading.Event()

        #self.job_is_running = threading.Event() # asdf
        self.sending_messages = threading.Event()
        self.InitFlags()

        ### the SocketProfile name will be defined after the connection established.
        self.mesgUnit = MesgHub.MesgUnitFactory( name='TBD', stat='N_A' )

        self.configs = runCONFIGs
    def InitFlags(self):
        self.server_socket_is_active.set()
        self.client_socket_is_active.set()

        # self.job_is_running.clear() # asdf
        self.sending_messages.clear()
    def SendMesg(self, socketCLIENT, mesg):
        self.sending_messages.set()
        socketCLIENT.sendall( MesgHub.SendSingleMesg(mesg) )
        self.sending_messages.clear()
def UpdateMesgAndSend( socketPROFILE:SocketProfile, socketCLIENT, newSTAT:str, newMESG:str='' ):
    socketPROFILE.mesgUnit.name = socketPROFILE.configs.name
    socketPROFILE.mesgUnit.stat = newSTAT
    socketPROFILE.mesgUnit.mesg = newMESG
    socketPROFILE.mesgUnit.t    = time.time()
    socketPROFILE.SendMesg(socketCLIENT, socketPROFILE.mesgUnit)
def SendTimeout(socketPROFILE:SocketProfile, socketCLIENT):
    the_stat = socketPROFILE.mesgUnit.stat
    UpdateMesgAndSend(socketPROFILE, socketCLIENT, the_stat)

def SystemCMDs(socketPROFILE:SocketProfile, cmdUNIT:MesgHub.CMDUnit):
    # emergent commands.
    if cmdUNIT.cmd == ConnCMD._STOP():
        LOG('Nothing to do', 'SystemCMDs', f'"STOP" command received from {cmdUNIT.name}. But nothing to do now.')
        return True
    if cmdUNIT.cmd == ConnCMD._FORCED_CLOSE_CURRENT_CONNECTION():
        socketPROFILE.client_socket_is_active.clear()
        return True
    # Not so emergent commands
    if cmdUNIT.cmd == ConnCMD._DESTROY():
        socketPROFILE.client_socket_is_active.clear()
        socketPROFILE.server_socket_is_active.clear()
        return True
    # Normal commands. Waiting for the previous command ended.
    return False


def handle_client(socketPROFILE:SocketProfile, clientSOCKET):
    try:
        while socketPROFILE.client_socket_is_active.is_set():
            if not clientSOCKET: break
            clientSOCKET.settimeout(SET_TIMEOUT)
            try:
                # Receive data from the client
                data = clientSOCKET.recv(MAX_MESG_LENG)
                if not data or data == b'':
                    continue
                rec_data = MesgHub.GetSingleMesg(data)

                if MesgHub.IsCMDUnit(rec_data):
                    # Process the command in a separate process
                    if SystemCMDs(socketPROFILE, rec_data):
                        UpdateMesgAndSend(socketPROFILE, clientSOCKET, 'Got SystCMD '+rec_data.cmd)
                        continue
                    # if socketPROFILE.job_is_running.is_set(): # asdf
                    #     LOG('Command Postponed', 'handle_client', f'the previous job is still processing. postpone new command {rec_data} until previous job finished')
                    #     socketPROFILE.job_is_running.wait()
                    process = threading.Thread(target=socketPROFILE.mainfunc, args=(socketPROFILE,clientSOCKET,rec_data,))
                    process.start()

            except socket.timeout:
                continue # totally disable the timeout message. Such that all message comes from the running message

                if socketPROFILE.sending_messages.is_set():
                    continue

                # Timeout reached, send current status to the client
                status_message = "Timeout reached. Current status: ... (implement your status here)"
                LOG('Status Mesg', 'handle_client', f'Sending command to client : {status_message}')
                SendTimeout(socketPROFILE, clientSOCKET)


    except Exception as e:
        LOG('Exception Raised', 'handle_client', f'Exception found {type(e)}: "{e}"')

    finally:
        # Close the client socket when done
        clientSOCKET.close()
        socketPROFILE.client_socket_is_active.set()

def execute_command(socketPROFILE:SocketProfile, clientSOCKET,command):
    #socketPROFILE.job_is_running.set() # asdf
    # Implement the logic to execute the command here
    # For demonstration purposes, this example simply prints the command
    # Send the current status back to the client
    status_message = f"Command '{command}' executed successfully."
    LOG('Job finished', 'execute_command', f'Sending mesg to client : {status_message}')

    mesg = MesgHub.CMDUnitFactory( name='execute_command', cmd='TESTING', arg=status_message)
    UpdateMesgAndSend( socketPROFILE, clientSOCKET, 'RUNNING', status_message)

    # socketPROFILE.job_is_running.clear() # asdf
    UpdateMesgAndSend( socketPROFILE, clientSOCKET, 'JOB_FINISHED')


DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 2000
def start_server(socketPROFILE:SocketProfile, theADDR=DEFAULT_IP, thePORT=DEFAULT_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((theADDR,thePORT))
    server_socket.listen(5)

    LOG('Start Server', 'start_server', f"Server listening on port {thePORT}...")

    try:
        while socketPROFILE.server_socket_is_active.is_set():
            client_socket, client_address = server_socket.accept()
            UpdateMesgAndSend(socketPROFILE, client_socket, 'INITIALIZED')
            handle_client(socketPROFILE,client_socket) # only allow a thread, not to use multithread

            # multi thread
            #if new_connection_analyzer(socketPROFILE,client_socket,client_address) != 0:
            #    time.sleep(SET_TIMEOUT)
            #    continue
            #print(f"Accepted connection from {client_address}")

            # Create a new thread to handle the client
            #client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            #client_thread.start()

    except KeyboardInterrupt:
        LOG('Forced Shutdown by Keyboard', 'SingleThreadListening', 'Service is shutting down...')
    finally:
        # Close the server socket when done
        LOG('Close the whole program', 'SingleThreadListening', '')
        server_socket.close()

if __name__ == "__main__":
    connection_profile = SocketProfile('selfTester',execute_command)
    start_server(connection_profile)
    '''
    not able to accept second connection if first connection losted.
    I thought this might come from the code keep sending message periodically. And no other connection able to be accepted
    '''

