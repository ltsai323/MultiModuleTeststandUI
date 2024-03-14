from threading import Lock
from flask import Flask, render_template, session
from flask_socketio import socketio, emit
from flask import Blueprint
from app_socketio import socketio
import requests
import tools.MesgHub as MesgHub

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.

app_b = Blueprint('bkgrun', __name__)
thread = None
thread_lock = Lock()


def background_thread(updateTIMER):
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(updateTIMER)
        count += 1
        #price = ((requests.get(url)).json())['data']['amount']
        socketio.emit('my_response',
                      {'data': 'backgroun updating ', 'count': count})

#@app_b.route('/flaskSOCKETio')
#def index_():
#    return render_template('index_flaskSocketIO.html', async_mode=socketio.async_mode)

@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})

# Receive the test request from client and send back a test response
@socketio.on('test_message')
def handle_message(data):
    print('received message: ' + str(data))
    emit('test_response', {'data': 'Test response sent'})

# Broadcast a message to all clients
@socketio.on('broadcast_message')
def handle_broadcast(data):
    print('received: ' + str(data))
    emit('broadcast_response', {'data': 'Broadcast sent'}, broadcast=True)

@socketio.event
#def connect():
def __connect():
    print('CONNNNNNNECT')
    UPDATE_TIMER = 0.3
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread, UPDATE_TIMER)
    emit('my_response', {'data': 'Connected', 'count': 0})

bkgevt_mesg_update = None
bkgevt_mesg_update_lock = Lock()
def Info( mesgHUB:MesgHub.MesgUnit ) -> dict:
    return {
            'indicator': mesgHUB.name,
            'theSTAT':    mesgHUB.stat,
            'message':   mesgHUB.mesg,
            'timestamp': mesgHUB.timestamp,
            }
def info(ii) -> dict:
    return {
            'indicator': 'aaa',
            'theSTAT':   'bbb',
            'message':   f'ccc {ii}',
            'timestamp': 'ddd',
            }
def message_update(updateTIMER):
    """Example of how to send server generated events to clients."""
    ii = 0
    while True:
        socketio.sleep(updateTIMER)
        #price = ((requests.get(url)).json())['data']['amount']
        ii += 1
        socketio.emit('bk', info(ii))

@socketio.event
#def activate_message_update():
#        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.1.3/socket.io.js" crossorigin="anonymous"></script>
#  this code activates the function
def connect():
    print('ACTIVATGELKSJDFKLSJDFKLJ')
    UPDATE_TIMER = 1.0
    global bkgevt_mesg_update
    with bkgevt_mesg_update_lock:
        if bkgevt_mesg_update is None:
            bkgevt_mesg_update = socketio.start_background_task(message_update, UPDATE_TIMER)
    socketio.emit('bk', info(-1))

def module_init(app):
    return None # do nothing
if __name__ == '__main__':
    app = Flask(__name__)

    @app_b.route('/')
    def index():
        return render_template('index_flaskSocketIO.html', async_mode=socketio.async_mode)
    app.register_blueprint(app_b)
    module_init(app_b)


    socketio.init_app(app)
    socketio.run(app)
