"""
This file offers a `socketio` object for as a global object.
As the example codes from Flask always uses global variable.
I'm using this file manages the socket variable
"""


from flask_socketio import SocketIO, emit
from datetime import datetime
async_mode = None
socketio = SocketIO(async_mode=async_mode, max_http_buffer_size=1e7)
import app_global_variables as gVAR
from flask import current_app


@socketio.on('soctest')
def socket_test():
    current_time = datetime.now().strftime("%H:%M:%S")
    emit('soctest_response', {'data': f'Server time: {current_time}'})


I = 0
@socketio.on('socket_get_web_status')
def socket_get_web_status():
    emit('socket_get_web_status_response', {'status': current_app.config['WEB_STAT'].btn} )
    #emit('socket_get_web_status_response', {'status': gVAR.WEB_STAT})

''' If you got error code 400
The error raised due to incompatible socket version from socket source and socket client.
https://flask-socketio.readthedocs.io/en/latest/intro.html#version-compatibility

Check flask-socketio version with `pip show flask-socketio`
>   Name: Flask-SocketIO
>   Version: 5.3.1
>   Summary: Socket.IO integration for Flask applications
>   Home-page: https://github.com/miguelgrinberg/flask-socketio
>   Author: Miguel Grinberg
>   Author-email: miguel.grinberg@gmail.com
>   License:
>   Location: /opt/homebrew/anaconda3/envs/flask/lib/python3.9/site-packages
>   Requires: Flask, python-socketio
>   Required-by:
And modify the loaded java script of socketio.
>   <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
https://cdn.socket.io/4.8.1/socket.io.min.js
'''

