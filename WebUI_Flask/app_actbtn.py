from flask import Flask, render_template, request, jsonify
#from app_2 import app_main_page
from dataclasses import dataclass
import socket
import tools.MesgHub as MesgHub
from tools.LogTool import LOG
import threading
from app_global_variables import _VARS_




from new_structure import UnitStageCommander
import subunit as subunit
from flask import Blueprint

app_b = Blueprint('action_button', __name__)

def Info( mesgHUB:MesgHub.MesgUnit ) -> dict:
    return {
            'indicator': mesgHUB.name,
            'theSTAT':    mesgHUB.stat,
            'message':   mesgHUB.mesg,
            'timestamp': mesgHUB.timestamp,
            }

@app_b.route('/buttonINITIALIZE', methods=['POST'])
def buttonINITIALIZE():
    for subunitName, subunitInstance in _VARS_.cmders.items():
        subunitInstance.Initialize()

    mesg_unit = app_b.pwrcmder.mesg
    indicator = mesg_unit.name
    mesg = mesg_unit.mesg
    test_new_mesg = mesg_unit.mesg

    return jsonify( Info(app_b.pwrcmder.mesg) )

@app_b.route('/buttonCONNECT', methods=['POST'])
def buttonCONNECT():
    for subunitName, subunitInstance in _VARS_.cmders.items():
        subunitInstance.Connect()

    mesg_unit = app_b.pwrcmder.mesg
    indicator = mesg_unit.name
    mesg = mesg_unit.mesg
    test_new_mesg = mesg_unit.mesg

    return jsonify( Info(app_b.pwrcmder.mesg) )

@app_b.route('/buttonDESTROY', methods=['POST'])
def buttonDESTROY():
    #app_b.pwrcmder.Destroy()
    for subunitName, subunitInstance in _VARS_.cmders.items():
        subunitInstance.Destroy()

    mesg_unit = app_b.pwrcmder.mesg
    indicator = mesg_unit.name
    mesg = mesg_unit.mesg
    test_new_mesg = mesg_unit.mesg

    return jsonify( Info(app_b.pwrcmder.mesg) )

def module_init(app):
    # SSH connector
    sshconn = subunit.PyModuleConnectionConfig('SSHTEST1', '192.168.50.60', 2000)
    sshconf = subunit.PyModuleCommandPool('../CommandPost/data/subunit_ssh_connect.yaml')
    sshunit = subunit.SubUnit(sshconn,sshconf)

    _VARS_.cmders['sshcmder'] = UnitStageCommander(sshunit)
    app.pwrcmder = _VARS_.cmders['sshcmder']


if __name__ == "__main__":
    app = Flask(__name__)

    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index_db.html')

    app.register_blueprint(app_b)
    module_init(app_b)

    from app_socketio import socketio
    socketio.init_app(app)
    socketio.run(app, host='0.0.0.0', port=8888)
