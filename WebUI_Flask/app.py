from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
import socket
from tools.MesgHub import MesgDecoder
from tools.LogTool import LOG
from datetime import datetime


app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    #return render_template('index.html')

    #current_datetime = datetime.now()
    #datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    #log = datetime_string + " | " + buttonClick_hub()
    return render_template('index_db.html')

logs = [
    "Log entry 1",
    "Log entry 2",
    "Log entry 3",
    # Add more log entries here if needed
]

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

    if button_id == 'btnCommandPCBI':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'BI')
    if button_id == 'btnCommandPCBC':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'BC')
    if button_id == 'btnCommandPCB1':
        raw_mesg = sendCMDTo(app.conn_ssh_connect, 'B1')


    print(raw_mesg)

    # Return a JSON response (optional)
    #return jsonify({'status': MesgDecoder(raw_mesg)})
    indicator, mesg = MesgDecoder(raw_mesg)
    LOG('RecvMesg', 'buttonClick_hub', f'indicator:{indicator}  --- message:{mesg}')
    return jsonify({'indicator':indicator, 'message':mesg})
    #return "Sample log from another device"


@app.route('/fetch_logs')
def fetch_logs():
    return "Sample log from another device"


def sendCMDTo(destnation, message):
    target_addr = destnation.ip
    target_port = destnation.port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((target_addr, target_port))
        s.sendall(message.encode())
        return s.recv(1024).decode('utf-8')

@dataclass
class ConnectConfigs:
    ip:str
    port:int
if __name__ == '__main__':
    # connection in docker
    #app.conn_power_supply = ConnectConfigs(ip='172.17.0.1',port=2235)
    #app.conn_ssh_hexactrl = ConnectConfigs(ip='172.17.0.1',port=2234)

    # connection directly executed
    app.conn_power_supply = ConnectConfigs(ip='127.0.0.1',port=2234)
    #app.conn_ssh_hexactrl = ConnectConfigs(ip='127.0.0.1',port=2234)


    #app.conn_power_supply = ConnectConfigs(ip='127.0.0.1',port=2000) # test module running in local
    #app.conn_power_supply = ConnectConfigs(ip='172.17.0.1',port=2001) # test module running in docker container
    app.conn_ssh_connect = ConnectConfigs(ip='127.0.0.1',port=2000)
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=8888, threaded=True)

