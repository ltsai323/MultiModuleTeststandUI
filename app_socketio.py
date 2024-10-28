"""
This file offers a `socketio` object for as a global object.
As the example codes from Flask always uses global variable.
I'm using this file manages the socket variable
"""


from flask_socketio import SocketIO
async_mode = None
socketio = SocketIO(async_mode=async_mode)

