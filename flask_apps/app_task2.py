import subprocess
import threading
import logging
from flask import Flask, render_template, request, jsonify, Blueprint

logger = logging.getLogger('flask.app')

#app = Flask(__name__)
app = Blueprint('app_task2', __name__)

server_status = {'status': 'idle'}
job_stop_flag = {'stop': False}
job_thread = {'thread': None}
def bb(val):
    logger.debug(f'checking point {val}')

def set_server_status(newSTAT):
    global server_status
    server_status['status'] = newSTAT
    bb(1)
def server_status_is(checkSTAT):
    bb(2)
    return server_status['status'] == checkSTAT
def server_is_runable():
    stat = server_status['status']
    runable_stat = [ 'idle', 'stopped' ]
    return True if stat in runable_stat else False

def run_command(cmd: str, jobID):
    logger.info(f"Starting command: {cmd}")
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    try:
        for line in process.stdout:
            logger.info(f'[{jobID}{line.strip()}')
            if job_stop_flag['stop']:
                logger.info(f"[{jobID}][Stop - Terminate]run_command() Stop signal received. Terminating command.")
                logger.info(f"[{jobID}][Stop - StatusChangeStopped]run_command() Error while running command: {e}")
                process.terminate()
                logger.info(f"[{jobID}][Stop - Terminate]run_command() process terminate sent.")
                break
        if not job_stop_flag['stop']:
            logger.info(f'[{jobID}][Run - StatusChangeIdle]run_command() Command "{cmd}" finished')
        bb(34)
    except Exception as e:
        logger.error(f'[{jobID}][Error - StatusChangeError]run_command() Error while running command: "{cmd}"')
        if server_status_is('stopping'):
            logger.info(f'[{jobID}][Error - StatusChangeError]run_command() error generated sinces "Stop" button clicked')
            set_server_status('stopped')
        else:
            logger.error(f'[{jobID}][Error - ErrorMessage     ] run_command() "{e}"')
        bb(33)
    finally:
        process.wait()
        set_server_status('idle')
        logger.info(f'[{jobID}][finally] run_command() sets system to idle')
        bb(32)
    bb(31)


def background_worker():
    global server_status, job_stop_flag
    job_stop_flag['stop'] = False
    set_server_status('running')

    try:
        command = "make run JobName=test1"
        #command = "sh scripts/run_single_module.sh hi 3"
        #command = " timeout 5s ping 8.8.8.8"
        #command = "make test theARRAY='test1 test2 test3'"
        run_command(command, 'Run')
        bb(43)
    finally:
        set_server_status('idle')
        logger.info("Job status set to idle.")
        bb(42)
    logger.info('background worker ended')
    bb(41)


@app.route('/main.html')
def main():
    return render_template('index_task2.html')


@app.route('/run', methods=['POST'])
def Run():
    global server_status
    logger.debug(f'[ServerAction][Run] Got an Run command')
    job_stop_flag = False
    if server_is_runable():
        logger.debug('[ServerAction][Run] the server status is idle, activate Run command')
        t = threading.Thread(target=background_worker)
        t.start()
        job_thread['thread'] = t
    else:
        logger.debug('[ServerAction][Run] Current status is {server_status["status"]}. reject "Run" command')
    bb(51)

    return '', 204


@app.route('/stop', methods=['POST'])
def Stop():
    job_stop_flag['stop'] = True
    logger.debug(f'[ServerAction][Stop] set job_stop_flag as True')
    set_server_status('stopping')
    bb(52)
    return '', 204


@app.route('/status')
def status():
    return jsonify(server_status)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='[basicCONFIG] %(levelname)s - %(message)s',
                        datefmt='%H:%M:%S')
    app_main = Flask(__name__)
    app_main.register_blueprint(app)
    
    @app_main.route("/")
    def index():
        return render_template("index_task2.html")
    bb(8)
    app_main.run(debug=True)
    bb(9)
