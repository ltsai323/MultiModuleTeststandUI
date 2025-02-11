from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
import queue
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# A thread-safe queue for log messages
log_queue = queue.Queue()

#import dd
proc_list = []


import sshconn
import bashcmd

def generate_messages():
    """
    Function that generates messages and puts them into the log queue.
    """
    #count = 0
    #while True:
    #    message = f"Generated message {count}"
    #    log_queue.put(message)
    #    count += 1
    #    time.sleep(5)  # Simulate some delay in message generation
    job_cmd_packs = []
    job_cmd_packs.append(sshconn.JobCMDPackFactory(log_queue, 'data/config_sshconn_sequentialjob.yaml'))
    job_cmd_packs[0].SetPar('boardtype', 'HD')
    job_cmd_packs[0].SetPar('boardID', 'asldkfjasldkf')

    job_cmd_packs.append(bashcmd.JobCMDPackFactory(log_queue, 'data/config_bashcmd_bkgjobmonitor.yaml'))
    #job_cmd_packs.append(bashcmd.JobCMDPackFactory(log_queue, 'data/config_bashcmd_bkgjobmonitor.yaml'))
    job_cmd_packs[1].SetPar('boardtype', 'HD')
    job_cmd_packs[1].SetPar('boardID', 'asldkfjasldkf')



    job_stat_list = []
    for job_cmd_pack in job_cmd_packs:
        job_stat = job_cmd_pack.execute(job_cmd_pack,'TEST')
        job_stat_list.append(job_stat)
        time.sleep(1.0)

def check_log_updates():
    """
    Function that checks the log queue for updates and emits them via WebSocket.
    """
    monitoring_period = 0.5
    while True:
        while not log_queue.empty():
            message = log_queue.get_nowait()
            socketio.emit('new_message', {'message': message}) # to do, send messages at one emit. Generate message to messages
        time.sleep(monitoring_period)  # Check every second for new messages

    '''
    keep_monitoring = True
    while keep_monitoring:
        keep_monitoring = False
        for proc in proc_list:
            if proc['process'].poll() is None:
                keep_monitoring = True

        while True:
            try:
                message = log_queue.get_nowait()
                socketio.emit('new_message', {'message': message})
            except queue.Empty:
                break
        time.sleep(monitoring_period)
    socketio.emit('new_mesage', {'message': 'all job finished'})
    '''

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to server'})

@socketio.on('start_execution')
def handle_start_execution():
    # Start the message generator thread only when this event is received
    if not hasattr(handle_start_execution, 'started'):
        message_thread = threading.Thread(target=generate_messages)
        message_thread.daemon = True
        message_thread.start()
        handle_start_execution.started = True
    emit('execution_started', {'data': 'Message generation started'})

if __name__ == "__main__":
    # Start the log checking thread
    log_thread = threading.Thread(target=check_log_updates)
    log_thread.daemon = True
    log_thread.start()

    print('[LinkAddress] http://localhost:5000')
    socketio.run(app, debug=True, port=5001)

