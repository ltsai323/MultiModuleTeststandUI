#!/usr/bin/env python3


import tools.MesgHub as MesgHub
import socket

def send_data(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_send:
        socket_send.connect(('127.0.0.1', 2000))
        mesg_init = MesgHub.CMDUnitFactory( name='sys1', cmd='INITIALIZE' )
        socket_send.send( MesgHub.SendSingleMesg(mesg_init) )
        data = socket_send.recv(1024)
        data = socket_send.recv(1024)
        data = socket_send.recv(1024)
        idx = 20
        while idx!=0:
            data = socket_send.recv(1024)
            #if False:
            if idx%5 == 0:
                mesg = f'sending mesg {idx}'
                mesg_init = MesgHub.CMDUnitFactory( name='test', cmd='TESTING', arg=mesg)
                socket_send.send( MesgHub.SendSingleMesg(mesg_init) )
            print(f'Response: {MesgHub.GetSingleMesg(data)}')

            idx-=1
        import tools.SocketCommands as ConnCMD
        print('send destroy command')
        #mesg_destroy = MesgHub.MesgUnitFactory( name='sys', stat='DESTROY', mesg='safely destroyed' )
        mesg_destroy = MesgHub.CMDUnitFactory( name='sys', cmd='DESTROY', arg='' )
        socket_send.sendall( MesgHub.SendSingleMesg(mesg_destroy) )
        print(mesg_destroy)

# Example usage
send_data('2')
