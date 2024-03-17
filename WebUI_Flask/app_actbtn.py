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
    for subunitName, subunitInstance in _VARS_.cmders.items():
        AddJob(subunitInstance.Initialize)
    return jsonify( Info(app_b.pwrcmder.mesg) )

@app_b.route('/buttonCONNECT', methods=['POST'])
def buttonCONNECT():
    for subunitName, subunitInstance in _VARS_.cmders.items():
        AddJob(subunitInstance.Connect)
    return jsonify( Info(app_b.pwrcmder.mesg) )

@app_b.route('/buttonCONFIGURE', methods=['POST'])
def buttonCONFIGURE():
    for subunitName, subunitInstance in _VARS_.cmders.items():
        AddJob(subunitInstance.Configure)
    return jsonify( Info(app_b.pwrcmder.mesg) )


@app_b.route('/buttonRUN', methods=['POST'])
def buttonRUN():
    AddJob(_VARS_.cmders['sshcmder'].Run)
    AddJob(_VARS_.cmders['testSSH'].Run)
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Job Sent', mesg='running jobs. waiting for the ended!') ) )

@app_b.route('/buttonTEST', methods=['POST'])
def buttonTEST():
    AddJob(_VARS_.cmders['sshcmder'].Test)
    AddJob(_VARS_.cmders['testSSH'].Test)
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Test Sent', mesg='running jobs. waiting for the ended!') ) )

@app_b.route('/buttonDESTROY', methods=['POST'])
def buttonDESTROY():
    _VARS_.cmders['testSSH'].Destroy()
    _VARS_.cmders['sshcmder'].Destroy()
    return jsonify( Info( MesgHub.MesgUnitFactory(name='FLASK', stat='Destroying', mesg='Signal sent. Waiting for updates.') ) )

def send_log_to_website(mesgUNIT:MesgHub.MesgUnit):
    global socketio
    print(f'send_log_to_website {mesgUNIT}')
    socketio.emit('bk', Info(mesgUNIT))
def socketio_sleep(sleepPERIOD):
    global socketio
    socketio.sleep(sleepPERIOD)

def module_init(app):
    # SSH connector
    sshconn = subunit.PyModuleConnectionConfig('SSHTEST1', '192.168.50.60', 2000)
    sshconf = subunit.PyModuleCommandPool('../CommandPost/data/subunit_ssh_connect.yaml')
    sshunit = subunit.SubUnit(sshconn,sshconf)

    _VARS_.cmders['sshcmder'] = UnitStageCommander(sshunit, send_log_to_website, socketio_sleep)
    app.pwrcmder = _VARS_.cmders['sshcmder']

    # SSH connector
    testsshconn = subunit.PyModuleConnectionConfig('SSHTEST2', '192.168.50.60', 2001)
    testsshconf = subunit.PyModuleCommandPool('../CommandPost/data/subunit_ssh_connect.yaml')
    testsshunit = subunit.SubUnit(testsshconn,testsshconf)

    _VARS_.cmders['testSSH'] = UnitStageCommander(testsshunit, send_log_to_website, socketio_sleep)
    app.pwrcmder = _VARS_.cmders['testSSH']

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
