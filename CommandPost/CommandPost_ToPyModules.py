import socket
import time
import threading
from tools.MesgHub import MesgDecoder_JSON as MesgDecoder
from tools.MesgHub import MesgEncoder_JSON as MesgEncoder
import tools.SocketCommands as SC

CONF_TIMEOUT = 3.0

#def mesg_rec(timeSTAMP,theMESG):
def MesgRec(timeSTAMP,theMESG):
    return (timeSTAMP,theMESG)
#def is_known_status(statusCODE):
def IsKnownStatus(statusCODE):
    if statusCODE > 0: return True
    return False
class PyModuleLog:
    def __init__(self,name,moduleADDR,modulePORT):
        self.name = name
        self.module_addr = moduleADDR
        self.module_port = modulePORT
        self.status = SC.N_A
        self.full_logs = []


class ConnectToPyModule:
    def __init__(self,*pymoduleLOG):
        self.modul_log = PyModuleLog(*pymoduleLOG)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(CONF_TIMEOUT)

        self.client_connected = threading.Event()
    def Initizlize(self):
        try:
            self.client_socket.connect( (self.module_addr,self.module_port) )
            self.status = SC.INITIALIZED
            self.full_logs.append( MesgRec('1', self.status[1]) )
            self.client_connected.set()
            LOG('Connection Initialized', 'ConnectToPyModule', f'Connection established to {self.module_log.module_addr}@{self.module_log.module_port}')
        except Exception as e:
            self.status = SC.ERROR
            self.full_logs.append( MesgRec('1',e) ) # asdf timestamp needed
            LOG('Error Raised', 'ConnectToPyModule', f'Error found {e}')

    def Destroy(self):
        self.client_connected.reset()
        if hasaddr(self,'client_socket'):
            self.client_socket.close()
            delattr(self,'client_socket')
            LOG('Destroy Connection To PyModule', 'ConnectToPyModule', f'Safely destroy the connection to "{self.name}"')

    def bkg_receive_data(self):



def client():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(3.0)  # Set a timeout for the accept call

    # Connect to the server
    client_socket.connect(("localhost", 2000))

    try:
        # Send data to the server
        mesg = {'name': 'bbc', 'mesg': '-SHUTDOWN-' }
        client_socket.sendall( MesgEncoder("Hello, server!") )

        print('value sent')

        # Receive data from the server
        data = MesgDecoder( client_socket.recv(1024) )
        print(f"Received from server: {data}")

        while True:
            try:
                data = MesgDecoder(client_socket.recv(1024) )
                print(f"Received periodical message from server: {data}")

                is_close = False
                for d in data:
                    if d['mesg'] == '-CLOSE-'
                        client_socket.close()
                        is_close = True
                if is_close: break

            except socket.timeout:
                break

        # Simulate a forced close scenario
        #client_socket.sendall("-CLOSE-".encode("utf-8"))
        mesg = {'name': 'bbc', 'mesg': '-SHUTDOWN-' }
        client_socket.sendall( MesgEncoder(mesg) )
        print("Sent close signal.")
        #client_socket.sendall("-FORCEDCLOSECONNECTION-".encode("utf-8"))
        #print("Sent forced close signal.")

        '''
        # Sleep for a while to allow the server to handle forced close
        time.sleep(2)
        client_socket.close()
        print('connect again')
        client_socket.connect(("localhost", 8888))

        # Send more data to the server
        client_socket.sendall("Another message after forced close.".encode("utf-8"))

        # Receive more data from the server
        data = client_socket.recv(1024).decode("utf-8")
        print(f"Received from server: {data}")
        '''

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the connection
        client_socket.close()
        print('close connection')

if __name__ == "__main__":
    client()

