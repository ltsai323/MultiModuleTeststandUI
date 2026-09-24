import subprocess
import threading
import logging
from flask import Flask, render_template, request, jsonify, Blueprint
from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms.validators import DataRequired, Regexp, InputRequired, NumberRange, AnyOf
from wtforms import StringField, SubmitField, RadioField, FloatField, IntegerField
import psycopg2
import flask_apps.shared_state as shared_state
from PythonTools.server_status import isCommandRunable
from datetime import datetime
import re
import os
from collections import deque

latest_running_batchNO = 0
latest_running_logs = deque(maxlen=8)
logs_lock = threading.Lock()
### HTTP status codes https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status

JOBMODE = 'task2' # IV scan

dirDAQresult = ''
DEFAULT_INSPECTORS = []

DBDatabase = None
DBHostname = None
DBPassword = None
DBUsername = None

SQL__CREATE_USED_FUNCTIONS = '''
CREATE OR REPLACE FUNCTION calculate_relative_humidity(
    t_c  double precision,
    td_c double precision
)
RETURNS double precision
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT
        100.0
        * exp(17.625 * td_c / (243.04 + td_c))
        / exp(17.625 * t_c  / (243.04 + t_c));
$$;
'''
def SQLfunc_check(cursor):
    cursor.execute("""
        SELECT to_regprocedure(
            'public.calculate_relative_humidity(double precision,double precision)'
        )
    """)

    if cursor.fetchone()[0] is None:
        cursor.execute(SQL__CREATE_USED_FUNCTIONS)
        logger.info(f'[CreateUsedSQLfunction] function "{public.calculate_relative_humidity}" decalred in database')


SQL__AVGTMP_AVGDEWP_AVGHUM = '''
-- read temperature and dew point from mmts_sensor_logging then average latest readout then calculate the humidity
-- return : avg_temp, avg_dewpoint, rel_humidity_in_percent


WITH latest_temp_readouts AS (
    SELECT DISTINCT ON (device_name)
        device_name,
        value::double precision AS value
    FROM public.mmts_sensors_logging
    WHERE device_name LIKE 'RTD-0%' AND timestamp_utc >= now() - INTERVAL '1 day'
    ORDER BY device_name, log_no DESC
),
latest_dew_point_readouts AS (
    SELECT DISTINCT ON (device_name)
        device_name,
        value::double precision AS value
    FROM public.mmts_sensors_logging
    WHERE device_name LIKE 'DMT-0%' AND timestamp_utc >= now() - INTERVAL '1 day'
    ORDER BY device_name, log_no DESC
),
averages AS (
    SELECT
        (SELECT AVG(value) FROM latest_temp_readouts) AS avg_temp,
        (SELECT AVG(value) FROM latest_dew_point_readouts) AS avg_dewpoint
)
SELECT
    COALESCE(avg_temp, 0) AS avg_temp,
    COALESCE(avg_dewpoint, 0) AS avg_dewpoint,
        CASE
        WHEN avg_temp IS NULL OR avg_dewpoint IS NULL THEN 0
        ELSE calculate_relative_humidity(avg_temp, avg_dewpoint)
    END AS rel_humidity_in_percent
FROM averages;
'''

SQL__NEWBATCHNAME_OLDBATCHNAME_CYCLECOUNT_RELATED_MODULEIDS = '''
-- prepare 2 kind of batch_name and cycle_count. Then providing RELATED MODULES FOR FURTHER CHECKING
-- note the returned value provides devs using new_batchname or old_batchname, once new_batchname is decided, you should use cycle_count as 1 or user input instead of using returned cycle_count.
-- return : new_batchname, old_batchname, cycle_count, module_names

SELECT DISTINCT ON (description)
  to_char( now(), 'YYYYMMDD-HH24MISS' ) AS new_batchname,
  batch_name AS old_batchname,
  cycle_count,
  module_names
FROM public.mmts_batch_logging
WHERE description = 'MMTSjobFinished'
ORDER BY description, batch_no DESC
'''




mmtsCONF = 'data/mmts_configurations.yaml'
external_URL = ''
external_URL_height = '200px'
thermalcycle_iterations = {}
try:
    with open(mmtsCONF, 'r') as fIN:
        import yaml
        conf = yaml.safe_load(fIN)
        external_URL = conf['externalURL']['IVCurveOnline']['URL']
        external_URL_height = conf['externalURL']['IVCurveOnline']['height']
        thermalcycle_iterations = conf['thermalcycle_iterations']

        dirDAQresult = f"{conf['DataLoc']}/daqplots/"
        DEFAULT_INSPECTORS = conf.get('Inspectors', [])
        DBDatabase = conf.get('DBDatabase', '')
        DBHostname = conf.get('DBHostname', '')
        DBPassword = conf.get('DBPassword', '')
        DBUsername = conf.get('DBUsername', '')


except FileNotFoundError as e:
    raise FileNotFoundError(f'\n\n[LackOfMMTSconf] Need to create configuration file "data/mmts_configuration.yaml"') from e

### intrinsic configuration would be defined in flask server instead of user input
INTRINSIC_CONF = [ ]
APP_CONFS = [
        'inspector',
        'cycleCOUNT',
        'moduleID1L',
        'moduleID1C',
        'moduleID1R',
        'moduleID2L',
        'moduleID2C',
        'moduleID2R',
        'moduleID3L',
        'moduleID3C',
        'moduleID3R',

        'moduleID4L',
        'moduleID4C',
        'moduleID4R',
        'moduleID5L',
        'moduleID5C',
        'moduleID5R',
        'moduleID6L',
        'moduleID6C',
        'moduleID6R',

        'moduleID7L',
        'moduleID7C',
        'moduleID7R',
        'moduleID8L',
        'moduleID8C',
        'moduleID8R',
]

def ExecCMD(jobID:str):
    make_command = 'make -n' if shared_state.debug_mode else 'make'
   #make_command = 'make -n'

    confDICT = shared_state.ReadConfigs(APP_CONFS)
    if jobID == 'Init':
        return f'{make_command} -f makefile_task2  initialize JobName=Init'
    if jobID == 'Run':
        shared_state.runidx+=1
        runTAG = f'run{shared_state.runidx}'
        dictOPTs = ' '.join([ f"{key}='{val}'" for key,val in confDICT.items() if val != '' ])

        ### a patch END
        return f'{make_command} -f makefile_task2  run ' + dictOPTs
    if jobID == 'Stop':
        return f'{make_command} -f makefile_task2  stop JobName=Stop'
    if jobID == 'Destroy':
        return f'{make_command} -f makefile_task2  destroy JobName=Destroy'



#logger = logging.getLogger('flask.app')
logger = logging.getLogger('werkzeug')


app = Blueprint('app_task2', __name__)


job_stop_flags = {
        'Init': threading.Event(),
        'Run': threading.Event(),
        'Stop': threading.Event(),
        'Destroy': threading.Event(),
        }

def bb(val):
    logger.warn(f'checking point {val}')
def check_jobmode() -> bool:
    logger.info(f'[CheckJobMode] coming jobmode {JOBMODE} and current status is {shared_state.jobmode}')
    if not shared_state.jobmode:
        logger.info(f'[ReplaceJobMode] jobmode modified from None to {JOBMODE}')
        shared_state.jobmode = JOBMODE
        return True

    if shared_state.jobmode == JOBMODE:
        logger.info(f'[CorrectJobMode] jobmode {JOBMODE} matched, keep running on')
        return True

    logger.warning(f'[InvalidJobMode] jobmode "{ shared_state.jobmode }" mismatched with local "{ JOBMODE }". Ignore command')
    return False



job_thread = {
        'Init': None,
        'Run': None,
        'Stop': None,
        'Destroy': None,
        }
def set_thread(runTYPE, tHREAD:threading.Thread):
    if runTYPE not in job_thread:
        logger.warning(f'[InvalidRunType] set_thread() got run type "{runTYPE}" but only "{ job_thread.keys() }" allowed')
        logger.warning(f'[InvalidRunType] set_thread() add "{runTYPE}" in the threading pool')

    if job_thread[runTYPE] and job_thread[runTYPE].is_alive():
        logger.warning(f'[JobIsRunning] set_thread() got running thread. waiting for previous thread finished')
        job_thread[runTYPE].join()

    job_thread[runTYPE] = tHREAD



def set_server_status(newSTAT):
    if shared_state.server_status == 'error': ## if error
        if newSTAT not in [ 'destroying', ]:
            return

    shared_state.server_status = newSTAT

def server_status_is(checkSTAT):
    return shared_state.server_status == checkSTAT

def run_command(cmd: str, jobID):
    """
    Executes a shell command in a subprocess, monitors its output line by line,
    and logs status messages including stop signals and errors.

    This function is designed to integrate with a server job control system.
    If a global ``job_stop_flags`` is set, the subprocess is terminated gracefully.
    It also updates the server status using ``set_server_status()`` and logs each
    step of execution.

    :param cmd: The shell command to run.
    :type cmd: str
    :param jobID: Identifier for the job, used in log messages.
    :type jobID: any
    :return: None
    :raises Exception: Logs any unexpected exception occurring during command execution.

    :Side Effects:
        - Starts a subprocess with ``cmd``.
        - Logs output line by line.
        - Terminates the subprocess if ``job_stop_flags`` is set.
        - Calls ``set_server_status()`` to manage server state transitions.

    :Logging:
        - Logs command start, each output line, stop signals, errors, and completion.
    """
    logger.info(f"[RunBashCMD][{jobID}] run_command executes command: {cmd}")
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
            logger.info(f'[{jobID}]{line.strip()}')
           #if jobID == 'Run': ## only record run job logs. These messages would be put on webpage
           #    with logs_lock:
           #        latest_running_logs.append(line.strip().rstrip("\r\n"))
                

            if job_stop_flags[jobID].is_set():
                logger.info(f"[{jobID}][Stop - Terminate]run_command() Stop signal received. Terminating command.")
                process.terminate()
                logger.info(f"[{jobID}][Stop - Terminate]run_command() process terminate sent.")
                break
        if not job_stop_flags[jobID].is_set():
            logger.info(f'[{jobID}][Run - StatusChangeIdle]run_command() Command "{cmd}" finished')
    except Exception as e:
        logger.error(f'[{jobID}][Error - StatusChangeError]run_command() Error while running command: "{cmd}"')

        process.terminate()
        if server_status_is('stopping'):
            logger.info(f'[{jobID}][Error - StatusChangeError]run_command() error generated sinces "Stop" button clicked')
        else:
            logger.error(f'[{jobID}][Error - ErrorMessage     ] run_command() "{e}"')
    finally:
        process.wait()
        if process.returncode == 0:
            set_server_status('idle')
            logger.info(f'[{jobID}][finally] run_command() sets system to idle')
        else:
            if not job_stop_flags[jobID].is_set():
                set_server_status('error')
                logger.info(f'[{jobID}][error] run_command() sets system to error. Please destroy and initialize it')
            else:
                logger.info(f'[{jobID}][stopped] run_command() jobs killed. so ignore the error message')




@app.route('/init', methods=['POST'])
def Init():
    ''' run bash command `make initialize` at background '''
    CMD_ID = 'Init'

    #logger.debug(f'[ServerAction][Init] Got an Init command')
    current_app.logger.debug(f'------------------- [ServerAction][Init] Got an Init command')

    if not check_jobmode(): return '', 204

    if isCommandRunable(shared_state.server_status,CMD_ID):
        set_server_status('initializing')
        job_stop_flags[CMD_ID].clear()
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] the server status is idle, activate {CMD_ID} command')

        def background_worker():
            try:
                command = ExecCMD(CMD_ID)
                #current_app.logger.debug(f'[bkg CMD Init] {command}')
                run_command(command, CMD_ID)
            finally:
                shared_state.DAQresult_current_modified = ''
                set_server_status('initialized')
                logger.info("Job status set to idle.")
            logger.info('background worker ended')


        t = threading.Thread(target=background_worker)
        t.start()
        set_thread(CMD_ID, t) # put to background running
    else:
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] Current status is {shared_state.server_status}. reject "{CMD_ID}" command')

    return '', 204

alphanumeric_validator = Regexp(r"^[a-zA-Z0-9-]*$", message="Only letters and numbers and dash allowed.")
class ConfigForm(FlaskForm):
    inspector = StringField("inspector", validators=[InputRequired(message='Inspector Missing')])
    cycleCOUNT = IntegerField("cycleCOUNT", validators=[InputRequired(message='Fill number of cycles'), NumberRange(min=0,max=1000, message='range from 0 to 1000')])

    moduleID1L = StringField("moduleID1L", validators=[alphanumeric_validator])
    moduleID1C = StringField("moduleID1C", validators=[alphanumeric_validator])
    moduleID1R = StringField("moduleID1R", validators=[alphanumeric_validator])
    moduleID2L = StringField("moduleID2L", validators=[alphanumeric_validator])
    moduleID2C = StringField("moduleID2C", validators=[alphanumeric_validator])
    moduleID2R = StringField("moduleID2R", validators=[alphanumeric_validator])
    moduleID3L = StringField("moduleID3L", validators=[alphanumeric_validator])
    moduleID3C = StringField("moduleID3C", validators=[alphanumeric_validator])
    moduleID3R = StringField("moduleID3R", validators=[alphanumeric_validator])

    moduleID4L = StringField("moduleID4L", validators=[alphanumeric_validator])
    moduleID4C = StringField("moduleID4C", validators=[alphanumeric_validator])
    moduleID4R = StringField("moduleID4R", validators=[alphanumeric_validator])
    moduleID5L = StringField("moduleID5L", validators=[alphanumeric_validator])
    moduleID5C = StringField("moduleID5C", validators=[alphanumeric_validator])
    moduleID5R = StringField("moduleID5R", validators=[alphanumeric_validator])
    moduleID6L = StringField("moduleID6L", validators=[alphanumeric_validator])
    moduleID6C = StringField("moduleID6C", validators=[alphanumeric_validator])
    moduleID6R = StringField("moduleID6R", validators=[alphanumeric_validator])

    moduleID7L = StringField("moduleID7L", validators=[alphanumeric_validator])
    moduleID7C = StringField("moduleID7C", validators=[alphanumeric_validator])
    moduleID7R = StringField("moduleID7R", validators=[alphanumeric_validator])
    moduleID8L = StringField("moduleID8L", validators=[alphanumeric_validator])
    moduleID8C = StringField("moduleID8C", validators=[alphanumeric_validator])
    moduleID8R = StringField("moduleID8R", validators=[alphanumeric_validator])
    submit = SubmitField("Configure")






@app.route('/submit', methods=['POST','GET'])
def Configure():
    CMD_ID = 'Configure'

    if not check_jobmode(): return '', 204
    if not isCommandRunable(shared_state.server_status,CMD_ID): return '', 204




    json_data = request.get_json()
    
    if not json_data:
        return jsonify({'status': 'error', 'message': 'Missing JSON data'}), 400


    form = ConfigForm(data=json_data)  # populate form with JSON data



    if not form.validate_on_submit():

        # Collect validation errors
        errors = {}
        for fieldName, errorMessages in form.errors.items():
            errors[fieldName] = errorMessages
        current_app.logger.warning(f'[Configure] Validation errors: {errors}')
        return jsonify({'status': 'error', 'errors': errors}), 400


    def ignore_special_characters(string):
        return re.sub(r'[^A-Za-z0-9\-]+', '', string) if string else '' ## allow capital characters, numbers
        #return re.sub(r'[^A-Za-z0-9]+', '', string) if string else '' ## allow capital characters, numbers and dash


    # Update CONF_DICT only if field has data
    form_vars = vars(form).keys()

    current_app.logger.debug(f'[LoadFormFromClient] Form "{vars(form)}"')

    shared_state.ClearConfig()
    for varname in APP_CONFS:
        if varname in INTRINSIC_CONF: continue ## pass some variable not from configuration

        value = getattr(form, varname).data if hasattr(form, varname) else ''
        current_app.logger.debug(f'[GotValue] Form {varname} got original value "{value}"')
        clean_val = ignore_special_characters(str(value)) if 'moduleID' in varname else str(value) ### only remove special character in moduleID
        if len(clean_val) > 20:
            current_app.logger.warning(f'[InputTooLong] Input {varname}:{clean_val} too long, resetting.')
            clean_val = ''
        shared_state.SetConfig(varname, clean_val)







    def conf_mesg():
        d = shared_state.ReadConfigs(APP_CONFS)
        input_modules = [ moduleID for dict_key, moduleID in d.items() if moduleID and 'moduleID' in dict_key ]
        moduleID_set = set()
        duplicates = set(x for x in input_modules if x in moduleID_set or moduleID_set.add(x))

        got_n_modules = len(input_modules)
        
        has_duplicate_moduleID = len(duplicates) != 0
        check1_mesg = f'\nHOWEVER duplicate modules:\n  {duplicates}' if has_duplicate_moduleID else '\nNo duplicate module'


        return f'''
got {got_n_modules} modules.

{check1_mesg}
'''



    is_empty_dict = sum( 1  if v else 0 for _,v in shared_state.ReadConfigs(APP_CONFS).items()) == 0
    if is_empty_dict:
        errors = 'Got empty configurations!'
        current_app.logger.warning(f'[Configure] {errors}')
        return jsonify({'status': 'error', 'errors': errors}), 400

    current_app.logger.info(f'[ConfigMessage] "{conf_mesg()}"')
    current_app.logger.info(f'[Configure] Current CONF_DICT: {shared_state.ReadConfigs(APP_CONFS)}')

    set_server_status('configured')
    # Return JSON with message, status 200 so client JS can alert
    return jsonify({'status': 'success', 'message': conf_mesg()}), 200




@app.route('/run', methods=['POST'])
def Run():
    ''' run bash command `make run` at background '''
    CMD_ID = 'Run'
    current_app.logger.debug(f'[ServerAction][{CMD_ID}] Got an {CMD_ID} command')
    if not check_jobmode(): return '', 204
    current_app.logger.debug(f'[ServerAction][{CMD_ID}] Got an {CMD_ID} command executing')

    job_stop_flags[CMD_ID].clear()
    if isCommandRunable(shared_state.server_status,CMD_ID):
        set_server_status('running')
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] the server status is idle, activate {CMD_ID} command')

        def background_worker():
            try:
                command = ExecCMD(CMD_ID)
                #current_app.logger.debug(f'[bkg CMD Run] {command}')
                run_command(command, CMD_ID)
            finally:
                set_server_status('idle')
                logger.info("Job status set to idle.")
            logger.info('background worker ended')


        t = threading.Thread(target=background_worker)
        t.start()
        set_thread(CMD_ID, t)
    else:
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] Current status is {shared_state.server_status}. reject "{CMD_ID}" command')

    return '', 204


@app.route('/stop', methods=['POST'])
def Stop():
    if not check_jobmode(): return '', 204
    CMD_ID = 'Stop'

    set_server_status('stopping')
    job_stop_flags['Run'].set()
    current_app.logger.debug(f'[ServerAction][Stop] set job_stop_flags as True')

    os.system('pkill make 2>/dev/null') ## force kill all jobs from make commands
    if job_thread['Run'] and job_thread['Run'].is_alive():
        job_thread['Run'].join()

    ## after command Run finished, reset the flag
    job_stop_flags['Run'].clear()

    def background_worker():
        try:
            command = ExecCMD(CMD_ID)
            #current_app.logger.debug(f'[bkg CMD Stop] {command}')
            run_command(command, CMD_ID)
        finally:
            set_server_status('idle')
            logger.info("Job status set to idle.")
        logger.info('background worker ended')

    t = threading.Thread(target=background_worker)
    t.start()
    t.join() # direct run without accept other command

    set_server_status('stopped')
    return '', 204

@app.route('/destroy', methods=['POST'])
def Destroy():
    if not check_jobmode(): return '', 204
    CMD_ID = 'Destroy'

    if isCommandRunable(shared_state.server_status,CMD_ID):
        set_server_status('destroying')
        for name, flag in job_stop_flags.items(): flag.set()
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] set ALL job_stop_flags as True')
        os.system('pkill make 2>/dev/null') ## force kill all jobs from make commands

        for name, t in job_thread.items():
            if t and t.is_alive():
                t.join() # waiting for all jobs finished

        ## after command Run finished, reset the flag
        for name, flag in job_stop_flags.items(): flag.clear()
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] reset ALL job_stop_flags')

        def background_worker():
            try:
                command = ExecCMD(CMD_ID)
                #current_app.logger.debug(f'[bkg CMD Destroy] {command}')
                run_command(command, CMD_ID)
            finally:
                logger.info("Destory ended")

        t = threading.Thread(target=background_worker)
        t.start()
        t.join() # direct run without accept other command

        set_server_status('destroyed')
    else:
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] Current status is {shared_state.server_status}. reject "{CMD_ID}" command')
    return '', 204

### asdf deleted?
@app.route('/status')
def status():
    hasupdate = False
    
    last_modified = os.path.getmtime(dirDAQresult)
    if last_modified != shared_state.DAQresult_current_modified:
        hasupdate = True
        shared_state.DAQresult_current_modified = last_modified
    
    ### if something updated, list all sub directories as list. Or return empty list
    daq_result_dirs = [ subdir for subdir in os.listdir(dirDAQresult) if os.path.isdir(f'{dirDAQresult}/{subdir}') ] if hasupdate else []
    return jsonify( {'status':shared_state.server_status, 'jobmode': shared_state.jobmode, 'DAQres': daq_result_dirs} )


@app.route('/main.html')
def main():
    daq_result_dirs = [ subdir for subdir in os.listdir(dirDAQresult) if os.path.isdir(f'{dirDAQresult}/{subdir}') ]
    return render_template('index_task2.html',
                           DAQres=daq_result_dirs,
                           currentCONF=shared_state.ReadConfigs(APP_CONFS),
                           ccc='',
                           IVCurveOnline_URL=external_URL,
                           IVCurveOnline_height=external_URL_height,
                           thermalCYCLE_iterationDICT = thermalcycle_iterations,
                           inspectors=DEFAULT_INSPECTORS,
                           )

@app.route("/logs")
def get_logs():
    """Return server-provided defaults for the Environment form."""
    global latest_running_batchNO
    with psycopg2.connect(
        dbname=DBDatabase,
        host=DBHostname,
        user=DBUsername,
        password=DBPassword,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f'''
WITH latest_logs AS (
SELECT batch_no, description FROM public.mmts_batch_logging
WHERE batch_no > {latest_running_batchNO}
ORDER BY batch_no DESC LIMIT 8
) SELECT batch_no, description FROM latest_logs ORDER BY batch_no ASC
            ''' )
            rows = cursor.fetchall()

            if len(rows) > 0:
                for _, mesg in rows:
                    if mesg:
                        latest_running_logs.append(mesg)
                latest_running_batchNO = int(rows[-1][0])
    with logs_lock:
        lines = list(latest_running_logs)

    response = jsonify(lines=lines)
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='[basicCONFIG] %(levelname)s - %(message)s',
                        datefmt='%H:%M:%S')
    app_main = Flask(__name__)
    app_main.register_blueprint(app, url_prefix='/task2')
    app_main.config["SECRET_KEY"] = '7eCZ^6nUxb6hjN5EbLYak&fvt'
    csrf = CSRFProtect(app_main)


    @app_main.route("/")
    def index():
        return render_template("index_task2.html")
    app_main.run(debug=True, port=5005)

