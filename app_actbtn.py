from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
import socket
import PythonTools.MesgHub as MesgHub
import threading
from app_global_variables import _VARS_, _LOG_CENTER_, _JOB_STAT_
from PythonTools.MyLogging_BashJob1 import log
#import app_bkgrun
import PythonTools.threading_tools as threading_tools

from flask_socketio import SocketIO, emit
from pprint import pprint
from app_socketio import socketio


import queue
from JobModule.JobStatus_main import JobStatus_JobSelect




from flask import Blueprint
from flask import current_app

app_b = Blueprint('action_button', __name__)


@app_b.route('/btnCONN', methods=['GET'])
def btn_connect() -> jsonify:
    '''
    Web client needs to click "connect" to fetch current status.

    Handles the button clicking. Once the client clicked "btnCONN", the server will send current status through jsonify

    * Output jsonify
        return jsonify({ 'btnSTATUS': self.btn, 'LEDs': self.LEDs, 'moduleIDs': self.moduleIDs })
    '''
    mesg = 'btnCONN clicked! send current webpage status to client'
    if hasattr(current_app, 'connected'):
        current_app.connected = True

    if hasattr(current_app, 'jobinstance'):
        ### keep original status
        pass
    else:
        current_app.jobinstance = JobStatus_JobSelect()
        current_app.config['WEB_STAT'].btn = current_app.jobinstance.status
        
        socketio.emit("start_periodic_update")
    current_app.config['MESG_LOG'].info(mesg)
    return current_app.config['WEB_STAT'].jsonify()


    
@socketio.on('btnINIT')
def btn_initialize(data):
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status

    Receiving data.get('jobmode', 'test') to get running info from radio form
    '''
    jobmode = data.get('jobmode', 'test')
    log.info(f'[Initialize Button] Set jobmode to "{ jobmode }"')
    print(f'\n\n\n[ status1 ] {current_app.jobinstance.status} \n\n ')

    current_app.jobinstance = current_app.jobinstance.Factory(jobmode)
    print(f'\n\n\n[ status2 ] {current_app.jobinstance.status} \n\n ')

    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    print(f'\n\n\n[ status3 ] {current_app.jobinstance.status} \n\n ')
    current_app.jobinstance.Initialize()
    print(f'\n\n\n[ status4 ] {current_app.jobinstance.status} \n\n ')
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    print(f'\n\n\n[ status5 ] {current_app.jobinstance.status} \n\n ')



    mesg = f'btnINIT clicked! waiting for all module initialized'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.jobinstance.status, 'log': mesg})

@app_b.route('/submit', methods=['POST'])
def buttonCONFIGURE():
    '''
    Configure function:
        When CONFIGURE button clicked from webpage, this function arised.
        There will be a message box raised.
        I should create information let user know the current configurations.

        Indeed this function is implemented by form + submit in html+javascript.

        (to do)
        At this stage, the webpage would send module IDs into this function.
        It is used to setup module into individual working unit.
        Furthermore, this stage put decides turn which working unit on and off.

        In the end, the output message forced user check the current configuration.
    '''
    IDs = request.form
    has = lambda ID: IDs[ID] != ""
    print(f'\n\n\n[IDs type] {type(IDs)}')
    print(f'\n\n\n[IDs type] {type(IDs.to_dict())}')
    print(IDs.to_dict())

    outMesg = f'''
    Configurations
    1L {has("moduleID1L")} \t1C {has("moduleID1C")} \t1R {has("moduleID1R")}
    2L {has("moduleID2L")} \t2C {has("moduleID2C")} \t2R {has("moduleID2R")}

    asdf BUT CURRENTLY NO ANY EFFECT asdf
    '''
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    current_app.jobinstance.Configure(IDs.to_dict())
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()

    current_app.config['MESG_LOG'].info(outMesg)
    
    ### javascript uses response.status to get contents inside the dict
    return jsonify( {'status':'success', 'message': outMesg} )
    #return jsonify( {'status':'type1 error', 'errors': 'blah blah'} )

@socketio.on('btnEXEC')
def btn_start():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    current_app.jobinstance.Run()
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()

    mesg = f'[btnEXEC] running all jobs'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.jobinstance.status, 'log': mesg})
@socketio.on('btnSTOP')
def btn_stop():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    mesg = f'[btnSTOP] stopping all jobs'
    emit('btnSTATUS', {'btnSTATUS': current_app.jobinstance.status, 'log': mesg})
    current_app.jobinstance.Stop()
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    current_app.config['MESG_LOG'].info(mesg)

    mesg = f'[btnSTOP] all job finished'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.jobinstance.status, 'log': mesg})
@socketio.on('btnEXIT')
def btn_destroy():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    current_app.jobinstance.Destroy()
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    mesg = f'[btnEXIT] Destroying job module'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.jobinstance.status, 'log': mesg})


    mesg = f'[btnEXIT] Destroyed'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.jobinstance.status, 'log': mesg})







if __name__ == "__main__":
    # create a simple flask server for testing
    app = Flask(__name__)

    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index_db.html')

    app.register_blueprint(app_b)
    #module_init(app_b)

    socketio.init_app(app)
    socketio.run(app, host='0.0.0.0', port=8888)
