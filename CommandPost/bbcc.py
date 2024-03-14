import socket
import time
from tools.MesgHub import MesgDecoder_JSON as MesgDecoder
from tools.MesgHub import MesgEncoder_JSON as MesgEncoder

def client():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect(("localhost", 2000))

    try:
        # Send data to the server
        #client_socket.sendall("Hello, server!".encode("utf-8"))

        print('value sent')


        client_socket.sendall( MesgEncoder("-FORCEDCLOSECURRENTCONNECTION-") )
        print("Sent forced close signal.")

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


