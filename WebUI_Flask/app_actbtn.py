from flask import Flask, render_template, request, jsonify
#from app_2 import app_main_page
from dataclasses import dataclass
import socket
import tools.MesgHub as MesgHub
from tools.LogTool import LOG
import threading
from app_global_variables import _VARS_
from app_bkgrun import AddJob

from app_socketio import socketio



from new_structure import UnitStageCommander
import subunit as subunit
from flask import Blueprint

app_b = Blueprint('action_button', __name__)

#def Info( mesgHUB:MesgHub.MesgUnit ) -> dict:
#    return {
#            'indicator': mesgHUB.name,
#            'theSTAT':   mesgHUB.stat,
#            'message':   mesgHUB.mesg,
#            'timestamp': mesgHUB.timestamp,
#            }
def Info( mesgHUB:MesgHub.MesgUnit ) -> dict:
    return {
            'indicator': mesgHUB.name,
            'theSTAT':    mesgHUB.stat,
            'message':   f'[{mesgHUB.name}] {mesgHUB.mesg}',
            'timestamp': mesgHUB.timestamp,
            }

@app_b.route('/buttonINITIALIZE', methods=['POST'])
def buttonINITIALIZE():
    jobTEMPLATE = '{}.Initialize'
    for subunitName, subunitInstance in _VARS_.cmders.items():
        AddJob(jobTEMPLATE.format(subunitName),subunitInstance.Initialize)
    return jsonify( Info(MesgHub.MesgUnitFactory(name='FLASK', stat='Initializing all modules', mesg='')) )

@app_b.route('/buttonCONNECT', methods=['POST'])
def buttonCONNECT():
    jobTEMPLATE = '{}.Connect'
    for subunitName, subunitInstance in _VARS_.cmders.items():
        AddJob(jobTEMPLATE.format(subunitName),subunitInstance.Connect)
    return jsonify( Info(MesgHub.MesgUnitFactory(name='FLASK', stat='Initializing all modules', mesg='')) )

@app_b.route('/buttonCONFIGURE', methods=['POST'])
def buttonCONFIGURE():
    jobTEMPLATE = '{}.Configure'
    return jsonify( Info(MesgHub.MesgUnitFactory(name='FLASK', stat='Configuring', mesg='Function Not Implemented')) )

    for subunitName, subunitInstance in _VARS_.cmders.items():
        AddJob(jobTEMPLATE.format(subunitName),subunitInstance.Configure)
    return jsonify( Info(MesgHub.MesgUnitFactory(name='FLASK', stat='Configuring', mesg='Configuring all modules')) )


@app_b.route('/buttonRUN', methods=['POST'])
def buttonRUN():
    jobTEMPLATE = '{}.Run'
    AddJob(jobTEMPLATE.format('SSHTEST1'),_VARS_.cmders['SSHTEST1'].Run)
    AddJob(jobTEMPLATE.format('SSHTEST2'),_VARS_.cmders['SSHTEST2'].Run)
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Job Sent', mesg='running all jobs.') ) )

@app_b.route('/buttonPAUSE', methods=['POST'])
def buttonPAUSE():
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Pause Job', mesg='function not implemented') ) )

@app_b.route('/buttonSTOP', methods=['POST'])
def buttonSTOP():
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Stop all jobs', mesg='Function not implemented') ) )

@app_b.route('/buttonTEST', methods=['POST'])
def buttonTEST():
    jobTEMPLATE = '{}.Test'
    AddJob(jobTEMPLATE.format('SSHTEST1'),_VARS_.cmders['SSHTEST1'].Test)
    AddJob(jobTEMPLATE.format('SSHTEST2'),_VARS_.cmders['SSHTEST2'].Test)
    print('jsonify:::', Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Test Sent', mesg='running all test jobs.') ) )
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Test Sent', mesg='running all test jobs.') ) )

@app_b.route('/buttonDESTROY', methods=['POST'])
def buttonDESTROY():
    jobTEMPLATE = '{}.Destroy'
    ## asdf error
    AddJob(jobTEMPLATE.format('SSHTEST2'),_VARS_.cmders['SSHTEST2'].Destroy)
    AddJob(jobTEMPLATE.format('SSHTEST1'),_VARS_.cmders['SSHTEST1'].Destroy)
    print('jsonfiy:::', Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Destroying', mesg='Signal sent. Waiting for updates.') ) )
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Destroying', mesg='Signal sent. Waiting for updates.') ) )


def module_init(app):
    global socketio
    class OverwriteBuildInFunc:
        from flask_socketio import SocketIO
        def __init__(self, socketIO:SocketIO):
            self.socketio = socketIO
        def log_method(self,mesgUNIT:MesgHub.MesgUnit):
            print(f'send_log_to_website {mesgUNIT}')
            self.socketio.emit('bkgRunJobs', Info(mesgUNIT))
        def sleep_func(self,sleepPERIOD):
            self.socketio.sleep(sleepPERIOD)
    new_log_and_sleep = OverwriteBuildInFunc(socketio)
    # SSH connector
    name='SSHTEST1'
    sshconn = subunit.PyModuleConnectionConfig(name, '192.168.50.60', 2000)
    sshconf = subunit.PyModuleCommandPool('../CommandPost/data/subunit_ssh_connect.yaml')
    sshunit = subunit.SubUnit(sshconn,sshconf)

    _VARS_.cmders[name] = UnitStageCommander(sshunit, new_log_and_sleep)
    #app.pwrcmder = _VARS_.cmders[name]

    # SSH connector
    name = 'SSHTEST2'
    testsshconn = subunit.PyModuleConnectionConfig(name, '192.168.50.60', 2001)
    testsshconf = subunit.PyModuleCommandPool('../CommandPost/data/subunit_ssh_connect.yaml')
    testsshunit = subunit.SubUnit(testsshconn,testsshconf)

    _VARS_.cmders[name] = UnitStageCommander(testsshunit, new_log_and_sleep)

if __name__ == "__main__":
    app = Flask(__name__)

    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index_db.html')

    app.register_blueprint(app_b)
    module_init(app_b)

    socketio.init_app(app)
    socketio.run(app, host='0.0.0.0', port=8888)
