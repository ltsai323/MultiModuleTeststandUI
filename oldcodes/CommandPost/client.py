import socket
import threading
from tools.MesgHub import MesgEncoder_JSON,MesgDecoder_JSON
import tools.SocketCommands as SOC_CMD
import time


def receive_feedback(client_socket):
    while client_socket:
        #feedback = client_socket.recv(1024).decode('utf-8')
        feedback = MesgDecoder_JSON(client_socket.recv(1024))
        if not feedback:
            break
        print(f"Received feedback from server: {feedback}")
def sendcmd_feedback(client_socket):
    idx = 0
    while True:
        # Get user input for the command
        command = input(f"Enter command (or '{SOC_CMD.CLOSE}' and '{SOC_CMD.SHUTDOWN}' to quit): ")
        mesg = MesgEncoder_JSON( {'name':'test', 'cmd':command } )

        # Send the command to the server
        client_socket.send(mesg)
        if command == SOC_CMD.CLOSE or command == SOC_CMD.SHUTDOWN:
            client_socket.close()
            break
        time.sleep(0.5)

def main():
    # Configure the client to connect to the server
    server_ip = '0.0.0.0'  # Replace with the actual server IP
    server_port = 2000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    # Start a thread to receive feedback from the server
    receive_thread = threading.Thread(target=receive_feedback, args=(client_socket,))
    sendcmd_thread = threading.Thread(target=sendcmd_feedback, args=(client_socket,))
    receive_thread.start()
    sendcmd_thread.start()
    receive_thread.join()
    sendcmd_thread.join()


    #client_socket.close()

if __name__ == "__main__":
    main()

