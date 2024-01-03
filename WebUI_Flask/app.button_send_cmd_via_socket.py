from flask import Flask, render_template
import socket

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index_button_send_cmd_via_socket.html')

@app.route('/send_message')
def send_message():
    message = "1"
    send_socket_message(message)
    return "Message sent: {}".format(message)
@app.route('/off_PS')
def status_off_powersupply():
    message = "0"
    send_socket_message(message)
    return "Message sent: {}".format(message)

def send_socket_message(message):
    #target_address = '127.0.0.1'
    #target_address = '172.17.0.1'
    #target_port = 2000 ## if use docker : the port follows docker run.
    target_address = '127.0.0.1'
    target_port = 2234 ## if use docker : the port follows docker run.

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((target_address, target_port))
        s.sendall(message.encode())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, threaded=True)

