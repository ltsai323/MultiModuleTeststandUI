from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
import socket
from tools.MesgHub import MesgDecoder
from tools.LogTool import LOG
import threading

app = Flask(__name__)

test_mesg = [
        'null mesg',
        ]
test_new_mesg = [
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        'asdalkdsjfalsdkfjasdfkl alkdf jaskldf kalsdf',
        ]

'''
def periodical_update_info():
    while not app.exit_code.is_set():
        time.sleep(1)
        for name, client in app.reg_clients.items():
            '''



@app.route('/')
def index():
    return render_template('index.html', messages = test_mesg)

@app.route('/buttonClick_hub', methods=['POST'])
def buttonClick_hub():
    button_id = request.form.get('button_id')

    raw_mesg = f'[Invalid buttonID] "{button_id}" not found'
    ## power supply
    if button_id == 'btnPowerSupply1':
        raw_mesg = sendCMDTo(app.conn_power_supply, '1')
    if button_id == 'btnPowerSupply0':
        raw_mesg = sendCMDTo(app.conn_power_supply, '0')


    if button_id == 'btnHexaControllerTT':
        print('[TEST] test button clicked')
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'TT')
    if button_id == 'btnHexaControllerhI':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'hI')
    if button_id == 'btnHexaControllerhC':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'hC')
    if button_id == 'btnHexaControllerh0':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'h0')
    if button_id == 'btnHexaControllerh1':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'h1')

    if button_id == 'btnCommandPCAI':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'AI')
    if button_id == 'btnCommandPCAC':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'AC')
    if button_id == 'btnCommandPCA1':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'A1')

    # orig
    #if button_id == 'btnCommandPCBI':
    #    raw_mesg = sendCMDTo(app.conn_ssh_connect, 'BI')
    #if button_id == 'btnCommandPCBC':
    #    raw_mesg = sendCMDTo(app.conn_ssh_connect, 'BC')
    #if button_id == 'btnCommandPCB1':
    #    raw_mesg = sendCMDTo(app.conn_ssh_connect, 'B1')

    # for test
    if button_id == 'btnCommandPCBI':
        print('asdf')
        raw_mesg = sendCMDTo(app.conn_tst_connect, 'BI')
    if button_id == 'btnCommandPCBC':
        raw_mesg = sendCMDTo(app.conn_tst_connect, 'BC')
    if button_id == 'btnCommandPCB1':
        raw_mesg = sendCMDTo(app.conn_tst_connect, 'B1')


    LOG('MesgSent', 'buttonClick_hub', raw_mesg)

    # Return a JSON response (optional)
    #return jsonify({'status': MesgDecoder(raw_mesg)})
    indicator, mesg = MesgDecoder(raw_mesg)
    LOG('RecvMesg', 'buttonClick_hub', f'indicator:{indicator}  --- message:{mesg}')
    return jsonify({'indicator':indicator, 'message':mesg, 'messages':test_new_mesg})

import time
@app.route('/update_messages')
def update_messages():
    # Simulate some delay (e.g., fetching data from a database or external source)
    time.sleep(2)

    return jsonify({'messages': test_new_mesg})

#def sendCMDTo(destnation, message):
#    target_addr = destnation.ip
#    target_port = destnation.port
#
#    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#        print('connection established')
#        s.connect((target_addr, target_port))
#        s.sendall(message.encode())
#        #return s.recv(1024).decode('utf-8')
#        return s.recv(1024)
def sendCMDTo(socket_dest, message):
    socket_dest.socket_client.sendall(message.encode())
    MMM = socket_dest.socket_client.recv(1024)
    print('test ', 'received mesg ', MMM)
    return MMM
    #return socket_dest.socket_client.recv(1024)

@dataclass
class conn_configs:
    ip:str
    port:int

def ConnectConfigs(ip='127.0.0.1', port=2000):
    c = conn_configs(ip=ip,port=port)
    c.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.socket_client.connect( (c.ip,c.port) )
    return c
if __name__ == '__main__':
    # connection in docker
    #app.conn_power_supply = ConnectConfigs(ip='172.17.0.1',port=2235)

    # connection directly executed
    #app.conn_power_supply = ConnectConfigs(ip='127.0.0.1',port=2000)


    #app.conn_power_supply = ConnectConfigs(ip='127.0.0.1',port=2000) # test module running in local
    #app.conn_power_supply = ConnectConfigs(ip='172.17.0.1',port=2001) # test module running in docker container
    app.conn_ssh_connect = ConnectConfigs(ip='127.0.0.1',port=2000)

    #app.conn_tst_connect = ConnectConfigs(ip='127.0.0.1',port=2000)

    #app.run(debug=True)
    app.run(host='0.0.0.0', port=8888, threaded=True)

