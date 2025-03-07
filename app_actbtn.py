from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
import socket
import PythonTools.MesgHub as MesgHub
from PythonTools.LogTool import LOG
import threading
from app_global_variables import _VARS_, _LOG_CENTER_, _JOB_STAT_
#import app_bkgrun
import PythonTools.threading_tools as threading_tools

from flask_socketio import SocketIO, emit
from pprint import pprint
from app_socketio import socketio


#import sshconn
#import bashcmd
#import rs232cmder_powersupply as rs232cmder
#import rs232cmder as rs232cmder
import queue




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
    if hasattr(current_app, 'jobinstance'):
        ### keep original status
        pass
    else:
        mesg = 'btnCONN clicked! you need to initialize all working modules for first'
        from JobModule.JobStatus_main import JobStatus_Startup
        from JobModule.JobStatus_base import JobStatus, JobConf

step0.functions.sh
sh test/step1.turnon_board_pwr.sh && sh test/step2.kria_env_setup.sh && sh test/step3.daqclient.sh
        cmd_templates = {
                'init_bashjob1': '',
                'init_bashjob2': 'echo hi22 {constVar}',
                'run_bashjob1': 'echo hi running',
                'run_bashjob2': 'echo hi22 running',
                'stop_bashjob1': 'kk',

                'init_bashjob1': '',
                'init_pwrjob2':  'poweron',
                'init_bashjob9': 'sh test/step1.turnon_board_pwr.sh && sh test/step2.kria_env_setup.sh && sh test/step3.daqclient.sh',

                'run_pwrjob1': '',
                'run_bashjob9': 'sh test/step4.takedata.sh',

                'stop_bashjob1': 'echo stopping',

                'destroy_bashjob1': 'sh test/step30.kill_daqclient.sh && sh test/step10.turnoff_board_pwr.sh',
                'destroy_pwrjob2': 'poweroff',
        }
        cmd_arg = {
                'initVar1': 'this is initVar1',
        }
        cmd_const = {
                'constVar': 'this is constant variable',
        }
        jobconf = JobConf(cmd_templates, cmd_arg, cmd_const)
        current_app.jobinstance = JobStatus_Startup(jobconf)
        
    current_app.config['WEB_STAT'].btn = current_app.jobinstance.status
    current_app.config['MESG_LOG'].info(mesg)
    return current_app.config['WEB_STAT'].jsonify()


    
@socketio.on('btnINIT')
def btn_initialize():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    current_app.jobinstance.Initialize()
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()



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
    outMesg = f'''
    Configurations
    1L {has("moduleID1L")} \t1C {has("moduleID1C")} \t1R {has("moduleID1R")}
    2L {has("moduleID2L")} \t2C {has("moduleID2C")} \t2R {has("moduleID2R")}

    asdf BUT CURRENTLY NO ANY EFFECT asdf
    '''
    current_app.jobinstance = current_app.jobinstance.fetch_current_obj()
    current_app.jobinstance.Configure({'initVar1': 'configured'})
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
