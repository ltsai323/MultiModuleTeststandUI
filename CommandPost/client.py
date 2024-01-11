import socket
import threading
from tools.MesgHub import MesgDecoder_JSON


def receive_feedback(client_socket):
    while True:
        feedback = client_socket.recv(1024).decode('utf-8')
        if not feedback:
            break
        print(f"Received feedback from server: {feedback}")

def main():
    # Configure the client to connect to the server
    server_ip = '0.0.0.0'  # Replace with the actual server IP
    server_port = 3000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    # Start a thread to receive feedback from the server
    receive_thread = threading.Thread(target=receive_feedback, args=(client_socket,))
    receive_thread.start()

    idx = 0
    while True:
        # Get user input for the command
        command = input("Enter command (or 'close' and 'shutdown' to quit): ")

        # Send the command to the server
        client_socket.send(command.encode('utf-8'))
        if command == 'close' or command == 'shutdown':
            break

    client_socket.close()

if __name__ == "__main__":
    main()

