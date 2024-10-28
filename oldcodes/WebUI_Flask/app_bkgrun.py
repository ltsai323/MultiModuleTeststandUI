from threading import Lock
from flask import Flask, render_template, session
from flask_socketio import emit
from flask import Blueprint
from app_socketio import socketio
import requests
import tools.MesgHub as MesgHub

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.

app_b = Blueprint('bkgrun', __name__)


from queue import Queue
job_queue = Queue()
bkgevt_job_queue = None
bkgevt_job_queue_lock = Lock()



bkgevt_mesg_update = None
bkgevt_mesg_update_lock = Lock()
def Info( mesgHUB:MesgHub.MesgUnit ) -> dict:
    return {
            'indicator': mesgHUB.name,
            'theSTAT':    mesgHUB.stat,
            'message':   f'[{mesgHUB.name}] {mesgHUB.mesg}',
            'timestamp': mesgHUB.timestamp,
            }
def info(ii) -> dict:
    return {
            'indicator': 'll',
            'theSTAT':   'BKG LOG',
            'message':   f'periodically show log {ii}',
            'timestamp': 'ddd',
            }
def message_update(updateTIMER):
    """Example of how to send server generated events to clients."""
    ii = 0
    while True:
        socketio.sleep(updateTIMER)
        ii += 1
        socketio.emit('bk', info(ii))

def execute_job_from_queue():
    JOB_CHECKING_TIMER = 1.0
    global job_queue
    while True:
        if job_queue.empty():
            socketio.sleep(JOB_CHECKING_TIMER)
        else:
            name, func, args, xargs = job_queue.get()
            socketio.emit('bkgRunJobs', Info( MesgHub.MesgUnitFactory(name='FLASK', stat=f'Run-Job', mesg=f'job "{name} is executing from queue"') ) )
            print('run job from queue', Info( MesgHub.MesgUnitFactory(name='FLASK', stat=f'Run-Job', mesg=f'job "{name} is executing from queue"') ) )
            func(*args, **xargs)
            socketio.emit('bkgRunJobs', Info( MesgHub.MesgUnitFactory(name='FLASK', stat=f'JobEnded', mesg=f'Ended job "{name}"') ) )
            print('finished job from queue', Info( MesgHub.MesgUnitFactory(name='FLASK', stat=f'JobEnded', mesg=f'Ended job "{name}"') ) )
            socketio.sleep(2.0)
            #input('End of bkg run job...')

def AddJob(jobNAME, jobFUNC, *args, **xargs):
    socketio.emit('Add job to queue', Info( MesgHub.MesgUnitFactory(name='FLASK', stat=f'NewJobAccepted', mesg=f'job "{jobNAME} put into queue"') ) )
    print('Add job to queue', MesgHub.MesgUnitFactory(name='FLASK', stat=f'NewJobAccepted', mesg=f'job "{jobNAME} put into queue"') )
    job_queue.put( (jobNAME, jobFUNC,args,xargs) )

#def activate_message_update():
#        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.1.3/socket.io.js" crossorigin="anonymous"></script>
#  this code activates the function
@socketio.event
def connect():
    UPDATE_TIMER = 5.0
    global bkgevt_mesg_update
    with bkgevt_mesg_update_lock:
        if bkgevt_mesg_update is None:
            bkgevt_mesg_update = socketio.start_background_task(message_update, UPDATE_TIMER)

    global bkgevt_job_queue, bkgevt_job_queue_lock
    with bkgevt_job_queue_lock:
        if bkgevt_job_queue is None:
            bkgevt_job_queue = socketio.start_background_task(execute_job_from_queue)

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
