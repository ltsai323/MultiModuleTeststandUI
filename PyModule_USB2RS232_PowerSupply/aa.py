import socket
import struct
import time
import threading

class ServerWithAnalyzer:
    def __init__(self, analyze_function):
        self.host = '127.0.0.1'
        self.port = 2000
        self.analyze_function = analyze_function

    def send_message(self, client_socket, message):
        message_length = len(message)
        packed_length = struct.pack("!I", message_length)
        client_socket.sendall(packed_length + message.encode('utf-8'))

    def receive_message(self, client_socket):
        packed_length = client_socket.recv(4)
        if not packed_length:
            return None

        message_length = struct.unpack("!I", packed_length)[0]
        message = client_socket.recv(message_length).decode('utf-8')
        return message

    def handle_client(self, client_socket, addr):
        print(f"Connection established with {addr}")

        try:
            idx=0
            while True:
                # Send status message every second
                status_message = f"Server status: OK {idx}"

                idx+=1
                self.send_message(client_socket, status_message)
                time.sleep(1)
                print(f'kkkk {idx}')

                # Receive command
                command = self.receive_message(client_socket)
                if command is not None:
                    print(f"Received command: {command}")
                    # Analyze the received command using the provided function
                    self.analyze_function(command)

        except ConnectionResetError:
            print("Client disconnected")
        finally:
            client_socket.close()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)

        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_handler.start()

if __name__ == "__main__":
    def analyze_function(command):
        print(f"Custom analysis of command: {command}")

    server_instance = ServerWithAnalyzer(analyze_function)
    server_instance.start_server()
