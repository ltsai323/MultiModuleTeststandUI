import socket
import threading
import time
import tools.StatusDefinition as STAT_DEF
import tools.SocketCommands as SOC_CMD
from tools.LogTool import LOG
from tools.MesgHub import MesgDecoder_JSON,MesgEncoder_JSON

from typing import Callable
BIND_ADDR = '0.0.0.0'
BIND_PORT = 2000

STAT_REPORT_PERIOD = 3

class message_center:
    name = '' # useful?

    status = ''
    updated = False
    message = ''
    def __init__(self, name):
        self.name = name
        self.status, self.message = STAT_DEF.N_A


class CommandPost:
    def __init__(self,recFUNC:Callable[[list],None], *statusHUB):
        '''
        recFUNC is a function used to handle received message from client
        The client should send a list of dictionary using json package.
        And the function is able to receive that and decide how to response
        statusHUB records the status of each individual modules
        '''
        self.receive_func = recFUNC

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((BIND_ADDR, BIND_PORT))
        self.server_socket.listen(5)
        self.server_socket.settimeout(2.0)

        self.orig_address = None
        self.self_mesg = message_center('self')
        self.mesgs = { s.name:s for s in statusHUB }
        LOG('Start Listening', 'CommandPost', f'listening {BIND_ADDR} @ port {BIND_PORT}')

    def run(self):
        LOG('run start', 'run', 'init')
        while True:
            if self.server_socket == None:
                LOG('Whole program is closed...', 'run', 'No server_socket object available.')
                break

            client_socket, address = self.server_socket.accept()
            LOG('new session', 'run', f'connected address {address}')

            if self.orig_address == None:
                # accept first connection
                self.orig_address = address
            elif self.orig_address != address:
                ## basically reject second connection. But if the second connection send "-FORCEDCLOSECURRENTCONNECTION-"
                ## command, disconnect current session
                # asdf no idea how to do
                #cmds = MesgDecoder_JSON(client_socket.recv(800)) # very small window for receive message
                #LOG('Refused connection', 'run', f'new connection from {address} refused')
                #for cmd in cmds:
                #    if cmd['cmd'] == SOC_CMD.FORCED_CLOSE_CURRENT_CONNECTION:
                #        client_socket.close()
                #        self.orig_address = None
                #        LOG('Clear current connection', 'cmd_receive_feedback', f'clear current connection')
                #        break
                continue
            LOG('Session accept', 'run', f"Accepted connection from {address}")

            # Start threads for sending and receiving
            #send_status_thread = threading.Thread(target=self.send_status_commands, args=(client_socket,))
            cmd_receive_thread = threading.Thread(target=self.cmd_receive_feedback, args=(client_socket,))

            #send_status_thread.start()
            cmd_receive_thread.start()

            # Wait for both threads to finish
            #send_status_thread.join()
            cmd_receive_thread.join()
            LOG('Session ended', 'run', f'connection from {address} ended')
    def run_(self):
        LOG('run start', 'run', 'init')

        # threading
        my_threads = []
        my_threads.append(threading.Thread(target=self.connection_handler))
        my_threads.append(threading.Thread(target=self.main_recv))

        for t in my_threads: t.start()
        for t in my_threads: t.join()

        #connection_handler()
        #main_recv()
        #periodically_report()

    def SetMesg(self,name,status,mesg):
        if not hasattr(self.mesgs, name):
            raise IOError(f'input message {name} not found')
        self.mesgs[name].updated = True
        self.mesgs[name].status  = status
        self.mesgs[name].message = mesg
    def AppendMesg(self,name,status,mesg):
        if not hasattr(self.mesgs, name):
            raise IOError(f'input message {name} not found')
        self.mesgs[name].updated = True
        self.mesgs[name].status  = status
        self.mesgs[name].message+= mesg



            # Accept a client connection
    def connection_handler(self):
        while True:
            if self.server_socket == None:
                LOG('Whole program is closed...', 'connection_handler', 'No server_socket object available.')
                return

            try:
                client_socket, address = self.server_socket.accept()
                LOG('new session', 'connection_handler', f'connected address {address}')

                if self.orig_address == None:
                    # accept first connection
                    self.client_socket = client_socket
                    self.orig_address = address
                    #self.client_socket.settimeout(2)
                    LOG('Session accept', 'run', f"Accepted connection from {address}")
                if self.orig_address != address:
                    ## basically reject second connection. But if the second connection send "-FORCEDCLOSECURRENTCONNECTION-"
                    ## command, disconnect current session
                    cmds = MesgDecoder_JSON(client_socket.recv(800)) # very small window for receive message
                    for cmd in cmds:
                        if cmd['cmd'] == SOC_CMD.FORCED_CLOSE_CURRENT_CONNECTION:
                            client_socket.close()
                            self.orig_address = None
                            LOG('Clear current connection', 'cmd_receive_feedback', f'clear current connection')
                            break
                    LOG('Refused connection', 'run', f'new connection from {address} refused')
            except:
                return
            #except socket.timeout:
            #    print('connection_handler timeout!!!!')
            #    time.sleep(2)


    def main_recv(self):
        while True:
            if self.server_socket == None:
                LOG('Whole program is closed...', 'main_recv', 'No server_socket object available.')
                return
            if self.orig_address == None:
                time.sleep(1)
                print('Waiting connection', 'main_recv', 'waiting for client connection...')
                continue

            # start communication
            #LOG('new session', 'run', f'connected address {address}')

            socket_connection = self.client_socket
            LOG('Connection Accepted', 'main_recv', 'from address "{self.orig_address}"')
            while True:
                try:
                    cmds = MesgDecoder_JSON(socket_connection.recv(1024))

                    print(f'Received command from client : {cmds}')
                    terminateThisSession = False
                    for cmd in cmds:
                        if not isinstance(cmd,dict):
                            LOG('Unknown input', 'CommandPost', f'Invalid command "{cmd}" received. Close this session.')
                            socket_connection.close()
                            self.orig_address = None
                            terminateThisSession = True
                            break
                        if cmd['cmd'] == SOC_CMD.CLOSE:
                            socket_connection.close()
                            LOG('Client Disconnected', 'CommandPost', f'Disconnect from {self.orig_address}, waiting for new connection...')
                            self.orig_address = None
                            terminateThisSession = True
                            break
                        if cmd['cmd'] == SOC_CMD.SHUTDOWN:
                            socket_connection.close()
                            self.server_socket.close()
                            self.server_socket = None
                            LOG('Shut down', 'main_recv', 'Received the request to shutdown the whole program')
                            return

                        LOG('Before modification', 'cmd_receive_feedback', f'current test mesg is : {self.mesgs["test"].message}')
                        self.receive_func(cmd,self.mesgs) # asdf need to use thread for parallel execution
                        LOG('After  modification', 'cmd_receive_feedback', f'current test mesg is : {self.mesgs["test"].message}')

                    if terminateThisSession: break

                except self.client_socket.timeout:
                    print('main_recv timeout!!!!')
                    pass
                except OSError as e: # if the connection is closed
                    print('section closed')
                    print(f'original addresss : {self.orig_address}. Client {self.client_socket}')

                    LOG('ERROR', 'main_recv', e)
                    time.sleep(2)
                    socket_connection.close()
                    self.orig_address = None
                    continue
    def cmd_receive_feedback(self,socket_connection):
        while True:
            try:
                cmds = MesgDecoder_JSON(socket_connection.recv(1024))

                print(f'Received command from client : {cmds}')
                for cmd in cmds:
                    if not isinstance(cmd,dict):
                        LOG('Unknown input', 'CommandPost', f'Invalid command "{cmd}" received. Close this session.')
                        socket_connection.close()
                        self.orig_address = None
                        return
                    if cmd['cmd'] == SOC_CMD.CLOSE:
                        socket_connection.close()
                        LOG('Client Disconnected', 'CommandPost', f'Disconnect from {self.orig_address}, waiting for new connection...')
                        self.orig_address = None
                        return
                    if cmd['cmd'] == SOC_CMD.SHUTDOWN:
                        socket_connection.close()
                        self.server_socket.close()
                        self.server_socket = None
                        LOG('Shut down', 'CommandPost', 'Received the request to shutdown the whole program')
                        return
                    LOG('Before modification', 'cmd_receive_feedback', f'current test mesg is : {self.mesgs["test"].message}')
                    self.receive_func(cmd,self.mesgs) # asdf need to use thread for parallel execution
                    LOG('After  modification', 'cmd_receive_feedback', f'current test mesg is : {self.mesgs["test"].message}')

            except OSError as e: # if the connection is closed
                print('section closed')
                socket_connection.close()
                return


    def send_status_commands(self,socket_connection):
        try:
            while True:
                time.sleep(STAT_REPORT_PERIOD)

                report = []
                for name, stat in self.mesgs.items():
                    if stat.updated == False: continue
                    report.append( { 'name':name, 'stat':stat.status, 'mesg':stat.message} )

                if len(report) == 0: continue
                socket_connection.sendall(MesgEncoder_JSON(*report))
        except OSError as e: # if the connection is closed
            print('section closed')
            return
        except (socket.error, BrokenPipeError):
            return # Ignore the process


if __name__ == "__main__":
    def command_pool(cmd, mesgHUB:dict): # command executed parallelly
        if cmd['name'] == 'test':
            print(f'hi test  sample received with command {cmd["cmd"]}')
            mesgHUB['test'].status = 3
            mesgHUB['test'].message = f'here is modified test message. Receiving the command "{cmd["cmd"]}"'

    obj1 = message_center('PowerSupply')
    obj2 = message_center('USB_RS232')
    obj3 = message_center('test')
    mainobj = CommandPost(command_pool, obj1,obj2,obj3)
    #mainobj.run()
    mainobj.run_()


