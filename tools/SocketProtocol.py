import socket
import threading
import sys
import time
from tools.MesgHub import MesgEncoder
from tools.LogTool import LOG
import tools.StatusDefinition as Status
import tools.SocketCommands as ConnCMD
MAX_MESG_LENG = 1024
DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 2000
SET_TIMEOUT = 1.0
def LOG(info,name,mesg):
    print(f'[{info} - LOG] (SocketProtocol-{name}) {mesg}', file=sys.stderr)

#def handle_client(theCONF,socket_send, addr, mainFUNC):
#    with socket_send:
#        LOG('', theCONF.name,f'Address {addr} connected')
#
#        while True:
#            data = socket_send.recv(MAX_MESG_LENG)
#            if not data:
#                break
#            input_data = data.decode('utf-8') # as a str
#            try:
#                #mainFUNC(theCONF,input_data, **mainARGS)
#                mesg = mainFUNC(theCONF,input_data)
#                LOG('Send Mesg', 'handle_client()', mesg)
#                socket_send.sendall(mesg.encode('utf-8'))
#            except ValueError as e:
#                LOG('Ignore', theCONF.name,e)
#
#                out_err = MesgEncoder('ERROR',e)
#                socket_send.sendall(out_err.encode('utf-8'))
CONNECTION_TIMEOUT=3
def new_connection_analyzer(self,socketCLIENT,newADDR):
    if not socketCLIENT: return -1

    socketCLIENT.settimeout(CONNECTION_TIMEOUT)
    LOG('Client Accessed', 'new_connection_analyzer',f'Address {newADDR} connected')
    try:
        data = socket_client.recv(MAX_MESG_LENG)
        LOG('Got data', 'handle_client', f'data: {data}')
        if data:
            input_data = MesgDecoder(data)

            if self.previousIP == None and input_data == ConnCMD.INITIALIZE:
                self.previousIP = newADDR
                LOG('Connected', 'new_connection_analyzer', f'Connection {newADDR} accepted.')
                return 0
            if input_data == ConnCMD.FORCED_CLOSE_CURRENT_CONNECTION:
                LOG('Forced Disconnected', 'new_connection_analyzer', f'Second connection {newADDR} disabled current connection {self.previousIP}')
                self.previousIP = None
                return 1 # new connection established. This command will be stopped here.
    except socket.timeout:
        LOG('Timeout', 'handle_client', 'time out reached! Stop connection {newADDR}')

    socketCLIENT.close() # if the connection established. Not to close this connection
    return -1
class SocketProtocol:
    def __init__(self, usedCONF, mainFUNC):
        self.conf = usedCONF
        self.main_func = mainFUNC
        self.status, self.mesg = Status.N_A
        self.previousIP = None
    def _mesg_interpreter__socketconnection_(self,address,mesg): # asdf
        '''
            if the returned value =-1: This is an unexpected connection. The command is stopped.
            if the returned value = 0: This is an old connection. pass the mesg to next step.
            if the returned value = 1: This is a new connection. Mesg will used in this stage. No mesg will be passed this time.
            if the returned value = 2: Another client requires force disconnection.
        '''
        Log('Checking Incoming Message', '_mesg_interpreter__socketconnection_', f'New connection {self.previousIP} found')
        if address == None: return -1

        if self.previousIP != address:
            if self.previousIP == None:
                # accept this connection
                if mesg == ConnCMD.INITIALIZE:
                    self.previousIP = address
                    LOG('Connected', '_mesg_interpreter__socketconnection_', f'Connection {address} accepted.')
                    return 1

            if mesg == ConnCMD.FORCED_CLOSE_CURRENT_CONNECTION:
                self.previousIP = None
                LOG('Forced Disconnected', '_mesg_interpreter__socketconnection_', f'Second connection {address} disabled current connection')
                return 2 # new connection established. This command will be stopped here.

            LOG('Forbidden Connection', '_mesg_interpreter__socketconnection_', f'New connection {address} are rejected.')
            return -1


        if mesg == ConnCMD.DESTROY:
            self.previousIP = None
            return 2
        return 0 # pass the command to be further interpreted.

    def handle_client(self,theCONF,socket_client, addr, mainFUNC):
        with socket_client:
            socket_client.settimeout(10)
            LOG('Client Accessed', theCONF.name,f'Address {addr} connected')

            while True:
                data = None
                try:
                    data = socket_client.recv(MAX_MESG_LENG)
                    LOG('Got data', 'handle_client', f'data: {data}')
                except socket.timeout:
                    #socket_client.sendall(f'status report {self.status}'.encode('utf-8'))
                    LOG('Timeout', 'handle_client', 'time out reached!')
                    continue

                if not data: continue

                if self._mesg_interpreter__socketconnection_(addr,input_data) != 0: continue

                try:
                    LOG('Data Received', 'handle_client', input_data)
                    #mainFUNC(theCONF,input_data, **mainARGS)
                    mesg = mainFUNC(theCONF,input_data)
                    LOG('Send Mesg', 'handle_client()', mesg)
                    socket_client.sendall(mesg.encode('utf-8'))
                except ValueError as e:
                    LOG('Ignore', theCONF.name,e)

                    out_err = MesgEncoder('ERROR',e)
                    socket_client.sendall(out_err.encode('utf-8'))
            LOG('Connection Closed', 'handle_client', f'connection to {addr} closed')
    def MultithreadListening(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            #socket_server.bind((self.conf.ip, self.conf.port))
            # the connection IP is a default value.
            # For direct running, it is a debug mode. Such as all of the running procedure is set the same ip address.
            # But if you want to activate multiple process. I'm putting it into docker container, which remap the 2000 port to 
            # another port in the 'docker run -p ' option.
            socket_server.bind((DEFAULT_IP,DEFAULT_PORT))

            socket_server.listen()

            while True:
                socket_client, addr = socket_server.accept()
                if new_connection_analyzer(self,socket_client, addr) != 0: continue
                client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(self.conf,socket_client, addr, self.main_func) ## asdf
                        )
                client_thread.start()
    def SingleThreadListening(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            socket_server.bind((DEFAULT_IP,DEFAULT_PORT))
            socket_server.listen()

            try:
                while True:
                    socket_client, addr = socket_server.accept()

                    self.handle_client(self.conf,socket_client, addr, self.main_func)

            except KeyboardInterrupt:
                LOG('Forced Shutdown by Keyboard', 'SingleThreadListening', 'Service is shutting down...')
            finally:
                socket_server.close()
    def SingleThreadListening_test(self):
        ## keep send command once, record the result, and sending message to the remote connection every second
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            socket_server.bind((DEFAULT_IP,DEFAULT_PORT))
            socket_server.listen(2)
            socket_server.settimeout(SET_TIMEOUT)


            while True:
                try:
                    socket_client, addr = socket_server.accept()
                    self.handle_client(self.conf,socket_client, addr, self.main_func)
                except socket.timeout:
                    time.sleep(1)

if __name__ == "__main__":
    def SendCMDToModule(theCONF, socketINPUT:str, nothing=''):
        LOG('connection established', 'Server side', f'Hi, a message received {socketINPUT}')

        return 'Connection established, welcome traveling to the server via socket'
    from dataclasses import dataclass
    @dataclass
    class Conf:
        name = str
        other_configs = int
    some_conf = Conf( name = 'test_config', other_configs = -1 )
    conn = SocketProtocol(some_conf, SendCMDToModule)

