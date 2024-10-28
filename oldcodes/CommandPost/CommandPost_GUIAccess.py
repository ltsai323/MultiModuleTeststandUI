import socket
import threading
import time
from tools.LogTool import LOG
from tools.MesgHub import MesgDecoder_JSON as MesgDecoder
from tools.MesgHub import MesgEncoder_JSON as MesgEncoder
from tools.MesgHub import MesgHub
#import tools.SocketCommands as SOC_CMD

CLOSE = '-CLOSE-' # use to close current socket connection to CommandPost
SHUTDOWN = '-SHUTDOWN-' # use to shutdown the CommandPost socket connection and quit this program

FORCED_CLOSE_CURRENT_CONNECTION = '-FORCEDCLOSECURRENTCONNECTION-'



def system_command_analyzer(connectionHANDLER, mesg, funcNAME, isOTHERconnection=False):
    is_a_system_command = False
    def del_connction(statMESG):
        if hasattr(connectionHANDLER,'first_connection'):
            connectionHANDLER.first_connection.send( MesgEncoder(CLOSE) )
            connectionHANDLER.first_connection.close()
            delattr(connectionHANDLER, 'first_connection')
            LOG(statMESG, 'system_command_analyzer', f'message "{mesg}" received. Close the connection to client from function {funcNAME}')
        else:
            LOG('Skip Command', 'system_command_analyzer', f'message "{mesg}" received. Close the connection to client from function {funcNAME}. But the client instance not found. Skip this command.')


    if mesg == FORCED_CLOSE_CURRENT_CONNECTION:
        connectionHANDLER.stop_current_connection.set()
        del_connction('Forced Client Connection Closed')
        return -1

    if isOTHERconnection: return 0 # if the connection from other connection. skip further checking

    if mesg == CLOSE:
        connectionHANDLER.stop_current_connection.set()
        del_connction('Client Connection Closed')
        return -1

    if mesg == SHUTDOWN:
        connectionHANDLER.exit_flag.set()
        connectionHANDLER.stop_current_connection.set()
        del_connction('Whole Program Shutdown')
        return -1

    return 0

class ConnectionHandler:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("localhost", 2000))
        self.server_socket.listen(2)
        self.server_socket.settimeout(3.0)  # Set a timeout for the accept call

        self.exit_flag = threading.Event()
        self.stop_current_connection = threading.Event()

        ''' additional instance "first_connection" will be attached inside this class '''

def accept_connections(connectionHANDLER):
    while not connectionHANDLER.exit_flag.is_set():
        try:
            client_socket, client_address = connectionHANDLER.server_socket.accept()
            LOG('New Connection', 'accept_connections', f"")

            if not hasattr(connectionHANDLER, 'first_connection'):
                LOG('Connection Accepted', 'accept_connections', f"a&c Accepted connection from {client_address}")
                connectionHANDLER.stop_current_connection.clear()
                connectionHANDLER.first_connection = client_socket
                second_thread = threading.Thread(target=subthread_accept_and_receive, args=(connectionHANDLER,client_socket,))
                second_thread.start()
            else:
                LOG('Additional Connection', 'accept_connections', 'New connection found')
                data = MesgDecoder( client_socket.recv(1024) )

                system_command_analyzer(connectionHANDLER, data, 'accept_connections', isOTHERconnection=True)
        except socket.timeout:
            pass
        except Exception as e:
            LOG('Error detected', 'accept_connections', f"Close current client due to error while accepting connection: {e}")
            system_command_analyzer(connectionHANDLER, CLOSE, 'ERROR-accept_connections')

def subthread_accept_and_receive(connectionHANDLER, client_socket):
    LOG('Service Activated', 'accept_and_receive', 'activated')
    while not connectionHANDLER.stop_current_connection.is_set():
        try:
            data = MesgDecoder( client_socket.recv(1024) )
            if system_command_analyzer(connectionHANDLER, data, 'accept_and_receive') == 0: continue
            LOG(f'Mesg', 'accept_and_receive', f'message received : "{data}"')

            if not data:
                continue
        except socket.timeout:
            pass
        except Exception as e:
            LOG('Error detected', 'subthread_accept_and_receive', f"Close current client due to error while accepting connection: {e}")
            system_command_analyzer(connectionHANDLER, CLOSE, 'ERROR-subthread_accept_and_receive')
            break
    client_socket.close()
    LOG('Service Stopped', 'accept_and_receive', 'stopped')
def send_feedback(connectionHANDLER):
    LOG('Service Activated', 'send_feedback', 's&f activated')
    while not connectionHANDLER.exit_flag.is_set():
        if not connectionHANDLER.stop_current_connection.is_set():
            if hasattr(connectionHANDLER, 'first_connection'):
                try:
                    connectionHANDLER.first_connection.sendall( MesgEncoder("Feedback message") )
                except Exception as e:
                    LOG('Error Found', 'send_feedback', f"s&f Error sending feedback: {e}")
                    break
        time.sleep(1)
    LOG('Service Stopped', 'send_feedback', 's&f stopped')

if __name__ == "__main__":
    handler_= ConnectionHandler()
    thread_accept = threading.Thread(target=accept_connections, args=(handler_,))
    thread_feedbk = threading.Thread(target=send_feedback, args=(handler_,))

    thread_accept.start()
    thread_feedbk.start()
    thread_accept.join()
    thread_feedbk.join()

