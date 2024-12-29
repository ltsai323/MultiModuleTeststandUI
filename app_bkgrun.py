'''
Set this variable to "threading", "eventlet" or "gevent" to test the
different async modes, or leave it set to None for the application to choose
the best option based on installed packages.
'''

from threading import Lock
from flask import Flask, render_template, session
from flask_socketio import emit
from flask import Blueprint
from app_socketio import socketio
import requests
import tools.MesgHub as MesgHub
from app_global_variables import _LOG_CENTER_, _VARS_
import app_global_variables as gVAR
import app_actbtn



app_b = Blueprint('bkgrun', __name__)

from DebugManager import BUG

import queue
job_queue = queue.Queue()
bkgevt_job_queue = None
bkgevt_job_queue_lock = Lock()

import re
def extract_mesg_from_log_center(inMESG) -> MesgHub.MesgUnit:
    '''
Convert input message to MesgHub.MesgUnit

Parameters
----------
inMESG : str
    Input message with template:

    "[mesg1][mesg2]mesg3"

    * mesg1 : module name who generate this message
    * mesg2 : brief status of this message
    * mesg3 : detail message

Returns
-------
MesgHub.MesgUnit
    '''
    pattern3 = r'\[(.*?)\] *\[(.*?)\](.*)'
    pattern2 = r'\[(.*?)\](.*)'

    inmesg = inMESG.strip()

    match3 = re.findall(pattern3, inmesg)
    if match3 and len(match3[0]) == 3:
        match = match3[0]
        return MesgHub.MesgUnitFactory(name=match[0], stat=match[1], mesg=match[2])

    match2 = re.findall(pattern2, inmesg)
    if match2 and len(match2[0]) == 2:
        match = match2[0]
        return MesgHub.MesgUnitFactory(name=match[0], stat='normal', mesg=match[1])

    return MesgHub.MesgUnitFactory(name='PatternNotRecoginzedERROR', stat='FailedExtractMesg', mesg=inmesg)



bkgevt_mesg_update = None
bkgevt_mesg_update_lock = Lock()
def Info( mesgHUB:MesgHub.MesgUnit ) -> dict:
    '''
Returned a directory used for flask.Jsonify generating a index.html

Parameters
----------
mesgHUB: MesgHub.MesgUnit
    Put name, status, mesg and timestampe to output dict.

Returns
-------
dict: python dictionary
    With format

    * indicator: Records where generates the message
    * theSTAT: Is a brief word showing the message
    * message: Is the detail message for indicating the result
    * timestamp mmm
    '''
    return {
            'indicator': mesgHUB.name,
            'theSTAT':    mesgHUB.stat,
            'message':   f'[{mesgHUB.name}]{mesgHUB.mesg}',
            'timestamp': mesgHUB.timestamp,
            }
def info(ii) -> dict:
    '''
As Info() do, but this function is only used for testing
    '''
    return {
            'indicator': 'll',
            'theSTAT':   'BKG LOG',
            'message':   ii,
            'timestamp': 'ddd',
            }
def message_update(updateTIMER):
    """
This is an function instance that keeps sending log to website.
This function should be executed at background thread.

Use socketio.sleep() instead of time.sleep() because socketio.sleep() would not stuck the whole thread but time.sleep() do.
    """
    global _LOG_CENTER_
    while True:
        try:
            latest_log = _LOG_CENTER_.get_nowait()
            socketio.emit('bkgRunJobs', Info( extract_mesg_from_log_center(latest_log) ))
        except queue.Empty:
            socketio.sleep(updateTIMER)

NORMAL_PRIORITY = 2
LOW_PRIORITY = 9
def execute_job_from_queue():
    '''
This is a function instance that keeps executing jobs in background threading.
It checks the current running status and `job_queue`. Once the running status is job-available,
this function executes the job from the `job_queue` sequentially.
However, you can also define a job not to block the queue.

Additionally, I need to implement a job priority mechanism. In previous code,
the code recorded `job_is_stucked`, with possible values of `True` or `False`.
I should modify it to use a range from `0` to `N`, where `0` has the greatest priority.
If a new action has a greater priority, this job can be processed first.

Job priorities are as follows:

- **0**: Destroy command
- **1**: Stop command
- **2**: Start / Run / Other command in sequence
- **9**: Commands that need to be running in the background (How do I prevent two low-priority commands from blocking each other?)
    '''
    def check_current_running_priority() -> int:
        # 0: not able to execute new job
        # 1: able to execute new job
        global _VARS_
        priority = LOW_PRIORITY
        for jobname, pymodule in _VARS_.cmders.items():
            if pymodule.jobstat:
                running_priority = pymodule.jobstat.AbleToAcceptNewJob()
                if running_priority == False:
                    priority = NORMAL_PRIORITY
                #running_priority = pymodule.jobstat.CurrentRunningPriority()
                #if running_priority < priority:
                #    priority = running_priority
        return priority


    JOB_CHECKING_TIMER = 1.0
    global job_queue
    global _VARS_
    latest_job_name = ''

    job_pending = None
    while True:
        socketio.sleep(JOB_CHECKING_TIMER)

        current_running_priority = check_current_running_priority()
        current_stat = app_b.web_stat

        BUG(f'current status is "{current_stat}"')
        if current_running_priority == LOW_PRIORITY:
            if current_stat == 'running' or current_stat == 'testing':
                # if new job is acceptable, update the status
                BUG(f'[AllJobFinished] Run or Test is finished, update server....')
                set_current_status('idle')

        if job_queue.empty() and job_pending == None:
            continue
        priority, name, func, args, xargs = job_pending if job_pending else job_queue.get()
        if priority < current_running_priority:
            job_pending = None
            socketio.emit('bkgRunJobs', Info( MesgHub.MesgUnitFactory(name='FLASK', stat='JobExecuting', mesg=f'executing job "{name}"') ) )
            func(*args, **xargs)
            latest_job_name = name
            # update current status here. Only update at job execution instead of button clicked.
            for jobname_identifier, btn_status in BTN_RENAME.items():
                if jobname_identifier in latest_job_name:
                    set_current_status(btn_status)
        else:
            job_pending = (priority, name, func, args, xargs)

def AddJob1(priority, jobNAME, jobFUNC, *args, **xargs):
    '''
Give a message to webpage before put job in queue
    '''
    BUG(f"[NewJobReceived] name:{jobNAME} has been put into queue")
    socketio.emit('bkgRunJobs', Info( MesgHub.MesgUnitFactory(name='FLASK', stat=f'NewJobAccepted', mesg=f'job "{jobNAME} put into queue"') ) )
    job_queue.put( (priority, jobNAME, jobFUNC,args,xargs) )
def AddJob(jobNAME, jobFUNC, *args, **xargs): # asdf
    '''
Put job in queue
    '''
    AddJob1(NORMAL_PRIORITY, jobNAME, jobFUNC, *args, **xargs)
def ClearJob():
    with job_queue.mutex:
        job_queue.queue.clear()
        BUG(f'all jobs are cleared by ClearJob() -------------------')
    BUG(f'leng of the job queue is {job_queue.qsize()}')

BUTTON_STATUS = {
        '': ['buttonINITIALIZE'],
        'none': ['buttonINITIALIZE'],
        'initialized'   : [                   'buttonCONFIGURE'                                         , 'buttonDESTROY'],
        'configured'    : [                   'buttonCONFIGURE', 'buttonTEST', 'buttonRUN'              , 'buttonDESTROY'],
        'running'       : [                                                                 'buttonSTOP', 'buttonDESTROY'],
        'testing'       : [                                                                 'buttonSTOP', 'buttonDESTROY'],
        'stopped'       : [                   'buttonCONFIGURE'                                         , 'buttonDESTROY'],
        'idle'          : [                   'buttonCONFIGURE'                                         , 'buttonDESTROY'],
        'destroyed'     : ['buttonINITIALIZE'],

        'errorfound'    : [                                                                               'buttonDESTROY'],
        'disabled'      : [],
        'btnclicked'    : [], # once any button clicked, disable everything until webpage returned status
        }
BTN_RENAME = {
        '.Initialize'   : 'initialized',
        '.Run'          : 'running',
        '.Test'         : 'testing',
        '.Stop'         : 'stopped',
        '.Destroy'      : 'destroyed',
        }

def set_current_status(btnSTAT) -> None:
    app_b.web_stat = btnSTAT
    BUG(f'Sending button status : {btnSTAT} and the available btns are {get_current_status()}')
    socketio.emit('button_status', get_current_status())
def get_current_status() -> list:
    return BUTTON_STATUS[app_b.web_stat]

@socketio.event
def connect():
    UPDATE_TIMER = 1.0
    global bkgevt_mesg_update
    with bkgevt_mesg_update_lock:
        if bkgevt_mesg_update is None:
            bkgevt_mesg_update = socketio.start_background_task(message_update, UPDATE_TIMER)

    global bkgevt_job_queue, bkgevt_job_queue_lock
    with bkgevt_job_queue_lock:
        if bkgevt_job_queue is None:
            bkgevt_job_queue = socketio.start_background_task(execute_job_from_queue)

    socketio.emit('bkgRunJobs', info(-1))

def module_init(app):
    """
Add two numbers.

Parameters
----------
a : int
    The first number.
b : int
    The second number.

Returns
-------
int
    The sum of a and b.
    """
    app_b.web_stat = 'none'

if __name__ == '__main__':
    app = Flask(__name__)

    @app_b.route('/')
    def index():
        return render_template('index_flaskSocketIO.html', async_mode=socketio.async_mode)
    app.register_blueprint(app_b)
    module_init(app_b)


    socketio.init_app(app)
    socketio.run(app)
