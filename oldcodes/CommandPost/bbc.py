import socket
import time
import threading
from tools.MesgHub import MesgDecoder_JSON as MesgDecoder
from tools.MesgHub import MesgEncoder_JSON as MesgEncoder

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

