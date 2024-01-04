from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
import socket

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buttonClick_hub', methods=['POST'])
def buttonClick_hub():
    button_id = request.form.get('button_id')

    mesg = 'nothing'
    if   button_id == 'btn1':
        mesg = 'Power Supply Activated'
        mesg = sendCMDTo(app.conn_power_supply, '1')
    elif button_id == 'btn2':
        mesg = 'Power Supply Deactivated'
        mesg = sendCMDTo(app.conn_power_supply, '0')
    elif button_id == 'btn3':
        mesg = 'Nothing Happened'
    else:
        mesg = f'[Invalid buttonID] "{button_id}" not found'

    print('btn pressed')

    # Return a JSON response (optional)
    return jsonify({'status': mesg})

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
    app.conn_power_supply = ConnectConfigs(ip='127.0.0.1',port=2000) # test module running in local
    #app.conn_power_supply = ConnectConfigs(ip='172.17.0.1',port=2001) # test module running in docker container
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=8888, threaded=True)

