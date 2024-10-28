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
import tools.MesgHub as MesgHub
import time

def send_data_and_print_feed_back(socketCONN, cmdUNIT:MesgHub.CMDUnit):
    print('b1')
    socketCONN.settimeout(1.0)
    try:
        socketCONN.sendall( MesgHub.SendSingleMesg(cmdUNIT) )
    except socket.timeout:
        print(f'TIMEOUT : send command {cmdUNIT}')

    print('b2')
    try:
        out = MesgHub.MesgDecoder_JSON( socketCONN.recv(1024) )
        print('b3')
        print(out)
    except socket.timeout:
        print(f'TIMEOUT : receive feedback timeout from {cmdUNIT}')
    print('b4')


# Example usage
if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_send:
        print('a1')
        socket_send.connect(('127.0.0.1', 2000))
        #send_data_and_print_feed_back(socket_send, MesgHub.CMDUnitFactory(name='aa', cmd='INITIALIZE') )
        print('a2')
        send_data_and_print_feed_back(socket_send, MesgHub.CMDUnitFactory(name='aa', cmd='connect') )
        time.sleep(3)
        print('a3')
        send_data_and_print_feed_back(socket_send, MesgHub.CMDUnitFactory(name='aa', cmd='test') )
        print('a4')
        time.sleep(3)
        send_data_and_print_feed_back(socket_send, MesgHub.CMDUnitFactory(name='aa', cmd='stop') ) # should terminate previous command
        print('a41')
        time.sleep(3)
        send_data_and_print_feed_back(socket_send, MesgHub.CMDUnitFactory(name='aa', cmd='test') ) # should no be executed
        print('a41')
        time.sleep(3)
        send_data_and_print_feed_back(socket_send, MesgHub.CMDUnitFactory(name='aa', cmd='DESTROY') )
        print('a5')
