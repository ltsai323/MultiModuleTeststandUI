import socket
import struct

def receive_message(client_socket):
    packed_length = client_socket.recv(4)
    if not packed_length:
        return None

    message_length = struct.unpack("!I", packed_length)[0]
    message = client_socket.recv(message_length).decode('utf-8')
    return message

def start_client():
    host = '127.0.0.1'
    port = 2000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        jjj = 10
        while True:
            received_message = receive_message(client_socket)

            jjj+=1
            if jjj == 15: continue
            mesg = f'sending mesg jjj {jjj}'
            print(mesg)
            client_socket.sendall(mesg.encode('utf-8'))
            if received_message is None:
                continue
            print(f"Received from server: {received_message}")
    except ConnectionResetError:
        print("Server disconnected")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()

