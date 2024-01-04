import socket
import threading
import sys
def LOG(info,name,mesg):
    print(f'[{info} - LOG] (SocketProtocol-{name}) {mesg}', file=sys.stderr)

def handle_client(theCONF,socket_send, addr, mainFUNC):
    with socket_send:
        LOG('', theCONF.name,f'Address {addr} connected')

        while True:
            data = socket_send.recv(theCONF.mesg_length)
            if not data:
                break
            input_data = data.decode('utf-8') # as a str
            try:
                #mainFUNC(theCONF,input_data, **mainARGS)
                mesg = mainFUNC(theCONF,input_data)
                LOG('Send Mesg', 'handle_client()', mesg)
                socket_send.sendall(('['+mesg+']').encode('utf-8'))
            except ValueError as e:
                LOG('Ignore', theCONF.name,e)

                out_err = f'[ERROR - {e}]'.encode('utf-8')
                socket_send.sendall(out_err)
class SocketProtocol:
    def __init__(self, usedCONF, mainFUNC):
        self.conf = usedCONF
        self.main_func = mainFUNC
    def MultithreadListening(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_listen:
            socket_listen.bind((self.conf.ip, self.conf.port))
            socket_listen.listen()

            while True:
                socket_send, addr = socket_listen.accept()
                client_thread = threading.Thread(
                        target=handle_client,
                        args=(self.conf,socket_send, addr, self.main_func) ## asdf
                        )
                client_thread.start()
