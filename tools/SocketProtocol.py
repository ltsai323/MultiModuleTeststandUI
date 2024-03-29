import socket
import threading
import sys
from tools.MesgHub import MesgEncoder
from tools.LogTool import LOG
MESG_LENG = 1024
def LOG(info,name,mesg):
    print(f'[{info} - LOG] (SocketProtocol-{name}) {mesg}', file=sys.stderr)

def handle_client(theCONF,socket_send, addr, mainFUNC):
    with socket_send:
        LOG('', theCONF.name,f'Address {addr} connected')

        while True:
            data = socket_send.recv(MESG_LENG)
            if not data:
                break
            input_data = data.decode('utf-8') # as a str
            try:
                #mainFUNC(theCONF,input_data, **mainARGS)
                mesg = mainFUNC(theCONF,input_data)
                LOG('Send Mesg', 'handle_client()', mesg)
                socket_send.sendall(mesg.encode('utf-8'))
            except ValueError as e:
                LOG('Ignore', theCONF.name,e)

                out_err = MesgEncoder('ERROR',e)
                socket_send.sendall(out_err.encode('utf-8'))
class SocketProtocol:
    def __init__(self, usedCONF, mainFUNC):
        self.conf = usedCONF
        self.main_func = mainFUNC
    def MultithreadListening(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_listen:
            #socket_listen.bind((self.conf.ip, self.conf.port))
            # the connection IP is a default value.
            # For direct running, it is a debug mode. Such as all of the running procedure is set the same ip address.
            # But if you want to activate multiple process. I'm putting it into docker container, which remap the 2000 port to 
            # another port in the 'docker run -p ' option.
            socket_listen.bind(('0.0.0.0', 2000))

            socket_listen.listen()

            while True:
                socket_send, addr = socket_listen.accept()
                client_thread = threading.Thread(
                        target=handle_client,
                        args=(self.conf,socket_send, addr, self.main_func) ## asdf
                        )
                client_thread.start()
