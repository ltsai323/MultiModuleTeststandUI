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

class SocketProtocol:
    def __init__(self, usedCONF, mainFUNC):
        self.conf = usedCONF
        self.main_func = mainFUNC
        self.status, self.mesg = Status.N_A
        self.previousIP = None
    def _mesg_interpreter__socketconnection_(self,address,mesg):
        '''
            if the return value ==-1 : This is an unexpected connection. The command is stopped.
            if the return value == 0 : This is an old connection. pass the mesg to next step.
            if the return value == 1 : This is a new connection. Mesg will used in this stage. No mesg will be passed this time.
        '''
        if self.previousIP == address: return 0 # old connection passing the mesg to next level

        # establish new connection
        if mesg == ConnCMD.CONNECT:
            self.previousIP = address
            self.status,self.mesg = Status.INITIALIZED
            return 1 # new connection established. This command will be stopped here.
        return -1 ## no corrected message. ignore the command
    def handle_client(self,theCONF,socket_client, addr, mainFUNC):
        with socket_client:
            socket_client.settimeout(1.0)
            LOG('', theCONF.name,f'Address {addr} connected')

            while True:
                data = None
                try:
                    data = socket_client.recv(MAX_MESG_LENG)
                except socket.timeout:
                    #socket_client.sendall(f'status report {self.status}'.encode('utf-8'))
                    #LOG('Timeout', 'handle_client', 'time out reached!')
                    continue
                if not data:
                    continue
                input_data = data.decode('utf-8') # as a str
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
            print('The connection closed')
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
                client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(self.conf,socket_client, addr, self.main_func) ## asdf
                        )
                client_thread.start()
    def SingleThreadListening(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            socket_server.bind((DEFAULT_IP,DEFAULT_PORT))
            socket_server.listen()
            #socket_server.

            while True:
                socket_client, addr = socket_server.accept()

                self.handle_client(self.conf,socket_client, addr, self.main_func)
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

