#!/usr/bin/env python3

'''
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_send:
    socket_send.connect(('127.0.0.1', 1234))
    socket_send.sendall(b'Hello, asldkfj')

    # 1024 is the maximum received data length
    data = socket_send.recv(1024)
    print(f'{data} received.')
'''

import socket

def send_data(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_send:
        socket_send.connect(('127.0.0.1', 2000))
        socket_send.sendall(message.encode('utf-8'))
        data = socket_send.recv(1024)
        print(f'Response: {data.decode("utf-8")}')

# Example usage
if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_send:
        socket_send.connect(('127.0.0.1', 2000))
        message = '[>-EstablishConnect-<]')
        socket_send.sendall(message.encode('utf-8'))
        data = socket_send.recv(1024)
        print(f'Response: {data.decode("utf-8")}')

