from flask import Flask, render_template, request, jsonify
from dataclasses import dataclass
import socket
import tools.MesgHub as MesgHub
from tools.LogTool import LOG
import threading
from app_global_variables import _VARS_, _LOG_CENTER_, _JOB_STAT_
#import app_global_variables as gVAR
#import app_bkgrun

from flask_socketio import SocketIO, emit
from pprint import pprint
from app_socketio import socketio

import sshconn
import bashcmd
#import rs232cmder_powersupply as rs232cmder
import rs232cmder as rs232cmder
import queue



from flask import Blueprint
from flask import current_app

app_b = Blueprint('action_button', __name__)

#from DebugManager import BUG, DEBUG_MODE

from DebugManager import BUG
DEBUG_MODE = True

def Info( mesgHUB:MesgHub.MesgUnit, btnSTAT:str ) -> dict:
    return {
            'indicator': mesgHUB.name,
            'theSTAT':    mesgHUB.stat,
            'message':   f'[{mesgHUB.name}] {mesgHUB.mesg}' if DEBUG_MODE else mesgHUB.mesg,
            'timestamp': mesgHUB.timestamp,
            'buttonSTATUS': BUTTON_STATUS[btnSTAT],
            }
def send_mesg_to_web( name, stat, mesg, err='', btnSTAT='btnclicked' ):
    #app_bkgrun.set_current_status(btnSTAT)
    return jsonify( {'indicator': name, 'status': stat, 'message': mesg, 'errors': err})

def AddJob(jobTEMPLATE, name, funcNAME):
    n = jobTEMPLATE.format(name)
    func = getattr(_VARS_.cmders[name], funcNAME)
    #app_bkgrun.AddJob(n, func) # need to handle priority
def AddJob1(priority,jobTEMPLATE, name, funcNAME):
    n = jobTEMPLATE.format(name)
    func = getattr(_VARS_.cmders[name], funcNAME)
    #app_bkgrun.AddJob1(priority,n, func)
@app_b.route('/btnCONN', methods=['GET'])
def btn_connect() -> jsonify:
    '''
    Web client needs to click "connect" to fetch current status.

    Handles the button clicking. Once the client clicked "btnCONN", the server will send current status through jsonify

    * Output jsonify
        return jsonify({ 'btnSTATUS': self.btn, 'LEDs': self.LEDs, 'moduleIDs': self.moduleIDs })
    '''
    mesg = 'btnCONN clicked! send current webpage status to client'
    if current_app.config['WEB_STAT'].btn == 'none':
        mesg = 'btnCONN clicked! you need to initialize all working modules for first'
        current_app.config['WEB_STAT'].btn = 'connected'
    current_app.config['MESG_LOG'].info(mesg)
    return current_app.config['WEB_STAT'].jsonify()

@socketio.on('btnINIT')
def btn_initialize():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    # orig function
    # current_app.config['btn'] = 'wait'
    # AddJob()

    ## testing without waiting job asdf
    current_app.config['btn'] = 'initialized'

    mesg = f'btnINIT clicked! waiting for all module initialized'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.config['btn'], 'log': mesg})

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

    Can I beautify this notification?
    '''
    current_app.config['MESG_LOG'].info(outMesg)
    
    ### javascript uses response.status to get contents inside the dict
    return jsonify( {'status':'success', 'message': outMesg, 'errors': 'no error'} )

@socketio.on('btnEXEC')
def btn_start():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    # current_app.config['btn'] = 'running'
    # AddJob()
    current_app.config['btn'] = 'running' # test without jobs asdf
    mesg = f'btnEXEC clicked!'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.config['btn'], 'log': mesg})
@socketio.on('btnSTOP')
def btn_stop():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    # current_app.config['btn'] = 'wait'
    # AddJob()
    current_app.config['btn'] = 'stopped' # test without jobs asdf
    mesg = f'btnSTOP clicked! waiting for stop function executed'
    current_app.config['MESG_LOG'].info(mesg)

    emit('btnSTATUS', {'btnSTATUS': current_app.config['btn'], 'log': mesg})
@socketio.on('btnEXIT')
def btn_destroy():
    '''
    Client sends command INITIALIZE to server. That the server should response the current button status
    
    Handles the button clicking. Once the client clicked "btnINIT", server side received the command INITIALIZE and update button status
    '''
    # current_app.config['btn'] = 'wait'
    # AddJob()
    current_app.config['btn'] = 'halt' # test without jobs asdf
    mesg = f'btnEXIT clicked! Destroy all executing modules'
    current_app.config['MESG_LOG'].info(mesg)
    emit('btnSTATUS', {'btnSTATUS': current_app.config['btn'], 'log': mesg})

#@app_b.route('/buttonINITIALIZE', methods=['POST'])
#def buttonINITIALIZE():
#    jobTEMPLATE = '{}.Initialize'
#
#    if DEBUG_MODE:
#        #AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , 'Initialize')
#        #AddJob(jobTEMPLATE, 'ModulePWRUpper'    , 'Initialize')
#        #AddJob(jobTEMPLATE, 'ModulePWRLower'    , 'Initialize')
#        AddJob(jobTEMPLATE, 'ctrlpc_bkg'        , 'Initialize')
#        AddJob(jobTEMPLATE, 'ctrlpc_seq'        , 'Initialize')
#
#        return send_mesg_to_web( name='btnINITIALIZE', stat='buttonClicked', mesg='Initializing python modules')
#
#        ### end of DEBUG_MODE
#
#    #for job_name, pyMODULE in _VARS_.cmders.items():
#    #    BUG(f'[initializing {job_name}')
#    #    n = jobTEMPLATE.format(job_name)
#    #    app_bkgrun.AddJob(n, pyMODULE.Initialize)
#
#    #return send_mesg_to_web( name='btnINITIALIZE', stat='buttonClicked', mesg='Initializing python modules')
#    AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , 'Initialize')
#    AddJob(jobTEMPLATE, 'ModulePWRUpper'    , 'Initialize')
#    AddJob(jobTEMPLATE, 'ModulePWRLower'    , 'Initialize')
#    AddJob(jobTEMPLATE, 'ntu8tester'        , 'Initialize')
#
#    return send_mesg_to_web( name='btnINITIALIZE', stat='buttonClicked', mesg='Initializing python modules')
#
#
#
#@app_b.route('/submit', methods=['POST'])
#def buttonCONFIGURE():
#    print('configured!!!')
#    '''
#    Configure function:
#        When CONFIGURE button clicked from webpage, this function arised.
#        There will be a message box raised.
#        I should create information let user know the current configurations.
#
#        (to do)
#        At this stage, the webpage would send module IDs into this function.
#        It is used to setup module into individual working unit.
#        Furthermore, this stage put decides turn which working unit on and off.
#
#        In the end, the output message forced user check the current configuration.
#    '''
#
#    IDs = request.form
#    #has = lambda ID: IDs[ID] != "" and IDs[ID] != "module ID"
#    has = lambda ID: IDs[ID] != ""
#    outMesg = f'''
#    Configurations
#    1L {has("moduleID1L")} 1C {has("moduleID1C")} 1R {has("moduleID1R")}
#    2L {has("moduleID2L")} 2C {has("moduleID2C")} 2R {has("moduleID2R")}
#    3L {has("moduleID3L")} 3C {has("moduleID3C")} 3R {has("moduleID3R")}
#
#    Can I beautify this notification?
#    '''
#    return send_mesg_to_web(name='hi', stat='configured', mesg=outMesg)
#    form_dict = AllAvailableInputFields()
#
#    for form_name, form in form_dict.items():
#        if form.validate_on_submit() == False:
#            BUG(f'[validation failed] {form_name}\n    ->  {form.errors}')
#            return send_mesg_to_web( name='configure', stat='error', mesg='Validation failed', err=f'[{form_name}] {form.errors}', btnSTAT='initialized')
#
#    recorded_value = {}
#    for form_name, form in form_dict.items():
#        recorded_value[form_name] = {opt_name: getattr(form, opt_name).data for opt_name in form._fields if opt_name != 'csrf_token' }
#        _VARS_.cmders[form_name].Configure(**recorded_value[form_name])
#        BUG(f'[valid submit - {form_name}]', recorded_value[form_name])  # Process the form data as needed
#
#    return send_mesg_to_web( name='configure', stat='success', mesg='Configure Successfully', btnSTAT='configured')
#
#
#@app_b.route('/buttonTEST', methods=['POST'])
#def buttonTEST():
#    jobTEMPLATE = '{}.Test'
#    jobINSTANCE = 'Test'
#
#
#    if DEBUG_MODE:
#        #AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#        AddJob(jobTEMPLATE, 'ctrlpc_bkg'        , jobINSTANCE)
#        AddJob(jobTEMPLATE, 'ctrlpc_seq'        , jobINSTANCE)
#
#        return send_mesg_to_web( name='btnTEST', stat='buttonClicked', mesg='Initializing python modules')
#
#    #for job_name, pyMODULE in _VARS_.cmders.items():
#    #    n = jobTEMPLATE.format(job_name)
#    #    app_bkgrun.AddJob(n, pyMODULE.Test)
#    #return send_mesg_to_web( name='btnTEST', stat='buttonClicked', mesg='Initializing python modules')
#    AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ntu8tester'        , jobINSTANCE)
#
#    return send_mesg_to_web( name='btnTEST', stat='buttonClicked', mesg='Initializing python modules')
#
#@app_b.route('/buttonRUN', methods=['POST'])
#def buttonRUN():
#    jobTEMPLATE = '{}.Run'
#    jobINSTANCE = 'Run'
#
#
#    if DEBUG_MODE:
#        #AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#        AddJob(jobTEMPLATE, 'ctrlpc_bkg'        , jobINSTANCE)
#        AddJob(jobTEMPLATE, 'ctrlpc_seq'        , jobINSTANCE)
#
#        return send_mesg_to_web( name='btnRUN', stat='buttonClicked', mesg='Executing jobs')
#
#    AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ntu8tester'        , jobINSTANCE)
#
#    return send_mesg_to_web( name='btnRUN', stat='buttonClicked', mesg='Executing jobs')
#
#@app_b.route('/buttonSTOP', methods=['POST'])
#def buttonSTOP():
#    jobTEMPLATE = '{}.Stop'
#    jobINSTANCE = 'Stop'
#    app_bkgrun.ClearJob()
#
#
#    if DEBUG_MODE:
#        AddJob1(0,jobTEMPLATE, 'ctrlpc_seq'        , jobINSTANCE)
#        AddJob1(0,jobTEMPLATE, 'ctrlpc_bkg'        , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#
#        return send_mesg_to_web( name='btnSTOP', stat='buttonClicked', mesg='All jobs are stopped')
#
#    #for job_name, pyMODULE in _VARS_.cmders.items():
#    #    n = jobTEMPLATE.format(job_name)
#    #    app_bkgrun.AddJob(n, pyMODULE.Stop)
#    ## prevent button status updated once clicked. Lock it as clicked!
#    #return send_mesg_to_web( name='btnSTOP', stat='buttonClicked', mesg='All jobs are stopped')
#    AddJob(jobTEMPLATE, 'ntu8tester'        , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#
#    return send_mesg_to_web( name='btnSTOP', stat='buttonClicked', mesg='All jobs are stopped')
#
#
#@app_b.route('/buttonDESTROY', methods=['POST'])
#def buttonDESTROY():
#    jobTEMPLATE = '{}.Destroy'
#    jobINSTANCE = 'Destroy'
#    app_bkgrun.ClearJob()
#
#
#    if DEBUG_MODE:
#        AddJob1(0,jobTEMPLATE, 'ctrlpc_bkg'        , jobINSTANCE)
#        AddJob1(0,jobTEMPLATE, 'ctrlpc_seq'        , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#        #AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#        return send_mesg_to_web( name='btnDESTROY', stat='buttonClicked', mesg='All jobs are stopped')
#
#
#    #for job_name, pyMODULE in _VARS_.cmders.items():
#    #    n = jobTEMPLATE.format(job_name)
#    #    app_bkgrun.AddJob(n, pyMODULE.Destroy)
#    #return send_mesg_to_web( name='btnDESTROY', stat='buttonClicked', mesg='All jobs are stopped')
#    AddJob(jobTEMPLATE, 'ntu8tester'        , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRUpper'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRLower'    , jobINSTANCE)
#    AddJob(jobTEMPLATE, 'ModulePWRHexaCtrl' , jobINSTANCE)
#    return send_mesg_to_web( name='btnDESTROY', stat='buttonClicked', mesg='All jobs are stopped')


def module_init(app):
    global socketio
    class OverwriteBuildInFunc:
        from flask_socketio import SocketIO
        def __init__(self, socketIO:SocketIO):
            self.socketio = socketIO
        def log_method(self,mesgUNIT:MesgHub.MesgUnit):
            BUG(f'send_log_to_website {mesgUNIT}')
            self.socketio.emit('bkgRunJobs', Info(mesgUNIT))
        def sleep_func(self,sleepPERIOD):
            self.socketio.sleep(sleepPERIOD)
    new_log_and_sleep = OverwriteBuildInFunc(socketio)

    global _LOG_CENTER_

    import JobStatManager
    class PyModule:
        def __init__(self, cmdPACK, stageCMD):
            self.cmdpack = cmdPACK
            self.stagecmd = stageCMD
            self.jobstat = None
        def Initialize(self):
            self.jobstat = self.stagecmd.Initialize(self.cmdpack, self.jobstat)
        def Configure(self, **argDICT):
            BUG(f'Configuring : {self.cmdpack.name}', argDICT)
            self.stagecmd.Configure(self.cmdpack, **argDICT)
        def Run(self):
            self.jobstat = self.stagecmd.Run(self.cmdpack, self.jobstat)
        def Test(self):
            self.jobstat = self.stagecmd.Test(self.cmdpack, self.jobstat)
        def Stop(self):
            self.jobstat = self.stagecmd.Stop(self.cmdpack, self.jobstat)
        def Destroy(self):
            self.jobstat = self.stagecmd.Destroy(self.cmdpack, self.jobstat)

    def add_to_global_var(jobNAME, cmdPACK, stageCMD):
        global _VARS_
        cmdPACK.name = jobNAME
        _VARS_.cmders[jobNAME] = PyModule(cmdPACK, stageCMD)





    jobqueue = queue.Queue()

    if DEBUG_MODE:
        #cmdpack  = rs232cmder.JobCMDPackFactory(_LOG_CENTER_, 'data/powersupplyUpper_config_rs232cmder.yaml')
        #stagecmd = rs232cmder.StageCMDFactory()
        #add_to_global_var('ModulePWRUpper', cmdpack, stagecmd)

        #cmdpack  = rs232cmder.JobCMDPackFactory(_LOG_CENTER_, 'data/powersupplyLower_config_rs232cmder.yaml')
        #stagecmd = rs232cmder.StageCMDFactory()
        #add_to_global_var('ModulePWRLower', cmdpack, stagecmd)

        #cmdpack  = rs232cmder.JobCMDPackFactory(_LOG_CENTER_, 'data/powersupplyHexaCtrl_config_rs232cmder.yaml')
        #stagecmd = rs232cmder.StageCMDFactory()
        #add_to_global_var('ModulePWRHexaCtrl', cmdpack, stagecmd)

        cmdpack = sshconn.JobCMDPackFactory(_LOG_CENTER_, 'data/ctrlpc_config_sshconn_sequentialjob.yaml')
        stagecmd = sshconn.StageCMDFactory()
        add_to_global_var('ctrlpc_seq', cmdpack, stagecmd)
        cmdpack = sshconn.JobCMDPackFactory(_LOG_CENTER_, 'data/ctrlpc_config_sshconn_bkgjobmonitor.yaml')
        stagecmd = sshconn.StageCMDFactory()
        add_to_global_var('ctrlpc_bkg', cmdpack, stagecmd)
        return


    cmdpack  = rs232cmder.JobCMDPackFactory(_LOG_CENTER_, 'data/powersupplyUpper_config_rs232cmder.yaml')
    stagecmd = rs232cmder.StageCMDFactory()
    add_to_global_var('ModulePWRUpper', cmdpack, stagecmd)

    cmdpack  = rs232cmder.JobCMDPackFactory(_LOG_CENTER_, 'data/powersupplyLower_config_rs232cmder.yaml')
    stagecmd = rs232cmder.StageCMDFactory()
    add_to_global_var('ModulePWRLower', cmdpack, stagecmd)

    cmdpack  = rs232cmder.JobCMDPackFactory(_LOG_CENTER_, 'data/powersupplyHexaCtrl_config_rs232cmder.yaml')
    stagecmd = rs232cmder.StageCMDFactory()
    add_to_global_var('ModulePWRHexaCtrl', cmdpack, stagecmd)

    cmdpack = sshconn.JobCMDPackFactory(_LOG_CENTER_, 'data/ntu8tester_config_sshconn_sequentialjob.yaml')
    stagecmd = sshconn.StageCMDFactory()
    add_to_global_var('ntu8tester', cmdpack, stagecmd)




def AllAvailableInputFields():
    import app_dynamic_form as dform
    o = {}
    for job_name, cmder in _VARS_.cmders.items():
        BUG(f'available input fields of {job_name} :', cmder.cmdpack.loaded_pars.parameters)
        dynamic_form_class = dform.UserInputFormFactory(job_name,cmder.cmdpack.loaded_pars.parameters)
        BUG(f'job name : {job_name}')
        o[job_name] = dynamic_form_class()
    return o




if __name__ == "__main__":
    # create a simple flask server for testing
    app = Flask(__name__)

    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index_db.html')

    app.register_blueprint(app_b)
    module_init(app_b)

    socketio.init_app(app)
    socketio.run(app, host='0.0.0.0', port=8888)
