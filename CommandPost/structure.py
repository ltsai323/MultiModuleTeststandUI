import socket
import threading
import time
import tools.StatusDefinition as STAT_DEF
from tools.LogTool import LOG
from typing import Callable
BIND_ADDR = '0.0.0.0'
BIND_PORT = 3000

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
                self.orig_address = address
            elif self.orig_address != address:
                LOG('Refused connection', 'run', f'new connection from {address} refused')
                continue
            # Accept a client connection
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




    def cmd_receive_feedback(self,socket_connection):
        while True:
            try:
                cmd = socket_connection.recv(1024).decode('utf-8')
                print(f'Received command from client : {cmd}')
                if cmd == 'close':
                    socket_connection.close()
                    LOG('Client Disconnected', 'CommandPost', f'Disconnect from {self.orig_address}, waiting for new connection...')
                    self.orig_address = None
                    return
                if cmd == 'shutdown':
                    socket_connection.close()
                    self.server_socket.close()
                    self.server_socket = None
                    LOG('Shut down', 'CommandPost', 'Received the request to shutdown the whole program')
                    return
                #self.receive_func(cmd,self.mesgs) # asdf

            except OSError as e: # if the connection is closed
                print('section closed')
                return


    def send_status_commands(self,socket_connection):
        idx = 0
        try:
            while True:
                time.sleep(STAT_REPORT_PERIOD)

                report = []
                for name, stat in self.mesgs.items():
                    if stat.updated == False: continue
                    report.append( { 'name':name, 'stat':stat.status, 'mesg':stat.message} )

                if len(report) == 0: continue
                # Send the status to the server
                status = '0' # asdf
                socket_connection.send(status.encode('utf-8'))
        except OSError as e: # if the connection is closed
            print('section closed')
            return
        except (socket.error, BrokenPipeError):
            return # Ignore the process


if __name__ == "__main__":
    def command_pool(cmds): # command executed parallelly
        for cmd in cmds:
            if cmd == '1': print('1 received')
            if cmd == '2': print('2 received')
            if cmd == '3': print('3 received')

    obj1 = message_center('PowerSupply')
    obj2 = message_center('USB_RS232')
    mainobj = CommandPost(command_pool, obj1,obj2)
    mainobj.run()


