import subprocess
import threading
import logging
from flask import Flask, render_template, request, jsonify, Blueprint
from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms.validators import InputRequired, Optional as OptionalV, NumberRange
from wtforms import StringField, SubmitField, IntegerField
import flask_apps.shared_state as shared_state
import flask_apps.kria_select as kria_select
from PythonTools.server_status import isCommandRunable
import re
import os
import sys
import yaml

JOBMODE = 'task4' # multi pedestal run: three hexaboards on one Kria, one slot at a time

### serial -> bring-up parameter table, shared with the bench scripts
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'scripts', 'task4_mmts_pedestal'))
import board_params  # noqa: E402

MMTS_CONF = 'data/mmts_configurations.yaml'
andrewCONF = f'{os.environ.get("AndrewModuleTestingGUI_BASE")}/configuration.yaml'
dirDAQresult = ''
DEFAULT_INSPECTORS = []
try:
    with open(andrewCONF, 'r') as fIN:
        conf = yaml.safe_load(fIN)
        DEFAULT_INSPECTORS = conf['Inspectors']
        dirDAQresult = f"{conf['DataLoc']}/daqplots/"
except FileNotFoundError as e:
    raise FileNotFoundError(f'\n\n[NoEnvVar] Need to `source ./init_bash_vars.sh` before execute this file') from e

BENCH = {}
try:
    with open(MMTS_CONF, 'r') as fIN:
        BENCH = (yaml.safe_load(fIN) or {}).get('MMTS_bench', {}) or {}
except FileNotFoundError:
    pass
SLOTS = [str(s) for s in BENCH.get('slots', ['A', 'B', 'C'])]

CONF_DICT = {
        'inspector': '',
        'moduleSTATUS': '',

        'moduleIDA': '',
        'moduleIDB': '',
        'moduleIDC': '',

        'powerBoardA': 'auto',
        'powerBoardB': 'auto',
        'powerBoardC': 'auto',

        'nRUNS': str(BENCH.get('default_nruns', 5)),
        'label': str(BENCH.get('default_label', 'ped')),
        'skipPROBE': str(BENCH.get('skip_probe', 1)),
        'bringupTRIES': str(BENCH.get('bringup_tries', 4)),
        }

### inspector and moduleSTATUS: parity with task1; no bench script reads them.
BENCH_KEYS = ['moduleIDA', 'moduleIDB', 'moduleIDC',
              'powerBoardA', 'powerBoardB', 'powerBoardC',
              'nRUNS', 'label', 'skipPROBE', 'bringupTRIES']


def ExecCMD(jobID:str, confDICT:dict):
    ### debug_mode prints each command instead of running it (no bench needed).
    make_command = 'make -n' if shared_state.debug_mode else 'make'
    make_command = kria_select.env_prefix() + make_command
    if jobID == 'Init':
        return f'{make_command} -f makefile_task4 initialize JobName=Init'
    if jobID == 'Run':
        shared_state.runidx += 1
        runTAG = f'run{shared_state.runidx}'
        dictOPTs = ' '.join([f"{key}='{val}'" for key, val in confDICT.items()
                             if key in BENCH_KEYS and val != ''])
        ### never -j: one Kria runs one slot at a time (one trigger claim).
        return f'{make_command} -f makefile_task4 run JobName=Run runTAG={runTAG} ' + dictOPTs
    if jobID == 'Stop':
        return f'{make_command} -f makefile_task4 stop JobName=Stop'
    if jobID == 'Destroy':
        return f'{make_command} -f makefile_task4 destroy JobName=Destroy'


def kill_local_make():
    """Kill this GUI's own make, the part makefile_task4's stop cannot reach.

    WARNING: the pattern is system-wide; under MMTS_DRYRUN this must signal nothing,
    or a test could kill a real run on the same machine.
    """
    if os.environ.get('MMTS_DRYRUN') == '1':
        logger.info('[dry-run] would pkill the local make')
        return
    os.system('pkill -f "[m]ake -f makefile_task4" 2>/dev/null')


logger = logging.getLogger('werkzeug')

app = Blueprint('app_task4', __name__)


job_stop_flags = {
        'Init': threading.Event(),
        'Run': threading.Event(),
        'Stop': threading.Event(),
        'Destroy': threading.Event(),
        }


def check_jobmode() -> bool:
    logger.info(f'[CheckJobMode] coming jobmode {JOBMODE} and current status is {shared_state.jobmode}')
    if not shared_state.jobmode:
        logger.info(f'[ReplaceJobMode] jobmode modified from None to {JOBMODE}')
        shared_state.jobmode = JOBMODE
        return True

    if shared_state.jobmode == JOBMODE:
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
        logger.warning(f'[InvalidRunType] set_thread() got run type "{runTYPE}"')

    if job_thread[runTYPE] and job_thread[runTYPE].is_alive():
        logger.warning(f'[JobIsRunning] set_thread() waiting for previous thread finished')
        job_thread[runTYPE].join()

    job_thread[runTYPE] = tHREAD


def set_server_status(newSTAT):
    shared_state.server_status = newSTAT


def server_status_is(checkSTAT):
    return shared_state.server_status == checkSTAT


# --------------------------------------------------------------------------
# Progress: parsed only from the "########## SLOT: stage" banners and exit codes.
# --------------------------------------------------------------------------
LED = {
    'queued': 'gray', 'starting': 'yellow', 'bringup': 'yellow', 'up': 'yellow',
    'gate': 'yellow', 'gated': 'yellow', 'pedestal': 'green', 'done': 'green',
    'failed': 'red', 'gate-failed': 'red',
}

EXIT_REASON = {
    '0': 'pedestals ran', '1': 'bring-up failed', '2': 'probe gave no summary',
    '3': 'registry or link map refused', '4': 'gate failed, pedestals not spent',
    '5': 'first pedestal stalled',
}

_BANNER = re.compile(r'^#{5,}\s+([A-C]):\s+(.*?)(?:\s+\[[^\]]*\])?\s*$')
_TRY = re.compile(r'^bringup try (\d+) of (\d+)')
_READY = re.compile(r'^READY\b(.*)')
_PEDROW = re.compile(r'^\d+ +\d{5,} ')


def reset_progress():
    shared_state.task4_slots.clear()
    shared_state.task4_log.clear()


def _slot(s):
    return shared_state.task4_slots.setdefault(
        s, {'slot': s, 'state': 'queued', 'led': LED['queued'], 'stage': 'queued',
            'params': '', 'peds': 0, 'nruns': 0, 'exit': None})


def _set(s, state, stage):
    d = _slot(s)
    d['state'] = state
    d['led'] = LED.get(state, 'gray')
    d['stage'] = stage
    return d


def parse_progress(line, current=None):
    """Fold one output line into shared_state.task4_slots. Returns the slot in play.

    `current` is the slot of the last banner; most other lines do not name one.
    """
    line = line.rstrip('\n')
    shared_state.task4_log.append(line)

    m = _BANNER.match(line)
    if m:
        s, rest = m.group(1), m.group(2)
        low = rest.lower()
        if low.startswith('params'):
            d = _set(s, 'starting', 'starting')
            d['params'] = rest[len('params'):].strip()
        elif low.startswith('bring-up') or low.startswith('second bring-up'):
            _set(s, 'bringup', 'bring-up')
        elif low.startswith('bringup failed') or low.startswith('second bringup failed'):
            _set(s, 'failed', 'bring-up failed')
        elif low.startswith('gate'):
            _set(s, 'gate', 'delay scan gate')
        elif low.startswith('12+12 probe'):
            _set(s, 'bringup', '12+12 probe')
        elif low.startswith('pedestal '):
            n = re.search(r'pedestal (\d+) of (\d+)', low)
            if n:
                d = _set(s, 'pedestal', f'pedestal {n.group(1)}/{n.group(2)}')
                d['nruns'] = int(n.group(2))
        elif low.startswith('pedestals '):
            n = re.search(r'pedestals \d+\.\.(\d+)', low)
            d = _set(s, 'pedestal', 'pedestals running')
            if n:
                d['nruns'] = int(n.group(1))
        elif low.startswith('first pedestal stalled'):
            _set(s, 'failed', 'first pedestal stalled')
        elif low.startswith('done'):
            _set(s, 'done', 'done')
        elif low.startswith('exit'):
            code = re.search(r'exit (\d+)', low)
            code = code.group(1) if code else '?'
            why = EXIT_REASON.get(code, f'run_slot.sh exited {code}')
            d = _set(s, 'done' if code == '0' else 'failed', why)
            d['exit'] = code
        else:
            _set(s, _slot(s)['state'], rest)
        return s

    if current is None:
        return current

    m = _TRY.match(line)
    if m:
        _set(current, 'bringup', f'bring-up try {m.group(1)} of {m.group(2)}')
        return current
    if _READY.match(line):
        _set(current, 'up', 'slot verified')
        return current
    if line.startswith('GATE: PASS'):
        _set(current, 'gated', 'gate passed')
        return current
    if line.startswith('GATE FAILED') or 'GATE: FAIL' in line:
        _set(current, 'gate-failed', 'gate failed')
        return current
    if _PEDROW.match(line):
        d = _slot(current)
        d['peds'] += 1
        if d['state'] == 'pedestal':
            d['stage'] = f"pedestal {d['peds']}/{d['nruns'] or '?'} done"
        return current
    return current


def run_command(cmd: str, jobID):
    """Run a shell command, streaming its output into the log and the slot states.

    Returns the exit code, so a refused preflight does not arm Run.
    """
    logger.info(f"[RunBashCMD][{jobID}] run_command executes command: {cmd}")
    shared_state.task4_log.append(f'$ {cmd}')
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    current = None
    try:
        for line in process.stdout:
            logger.info(f'[{jobID}]{line.rstrip()}')
            current = parse_progress(line, current)

            if job_stop_flags[jobID].is_set():
                logger.info(f"[{jobID}][Stop - Terminate] Stop signal received. Terminating command.")
                process.terminate()
                break
        if not job_stop_flags[jobID].is_set():
            logger.info(f'[{jobID}][Run - StatusChangeIdle] Command "{cmd}" finished')
    except Exception as e:
        logger.error(f'[{jobID}][Error] while running command: "{cmd}"')
        process.terminate()
        if server_status_is('stopping'):
            logger.info(f'[{jobID}][Error] error generated since "Stop" button clicked')
        else:
            logger.error(f'[{jobID}][Error - ErrorMessage] run_command() "{e}"')
    finally:
        process.wait()
        set_server_status('idle')
        logger.info(f'[{jobID}][finally] run_command() sets system to idle')
    return process.returncode


@app.route('/init', methods=['POST'])
def Init():
    ''' run bash command `make initialize` at background '''
    CMD_ID = 'Init'
    current_app.logger.debug(f'[ServerAction][{CMD_ID}] Got an {CMD_ID} command')

    if not check_jobmode(): return '', 204

    if isCommandRunable(shared_state.server_status, CMD_ID):
        ### the Kria picked on the page; it holds until the next Initialize
        try:
            kria_select.select((request.get_json(silent=True) or {}).get('kria', shared_state.kria_ip))
        except ValueError as e:
            shared_state.task4_log.append(f'*** {e}')
            return jsonify({'status': 'error', 'message': str(e)}), 400
        set_server_status('initializing')
        job_stop_flags[CMD_ID].clear()
        reset_progress()

        def background_worker():
            rc = 1
            try:
                command = ExecCMD(CMD_ID, CONF_DICT)
                rc = run_command(command, CMD_ID)
            finally:
                shared_state.DAQresult_current_modified = ''
                ### refused preflight: 'error' blocks Configure and Run until Destroy.
                if rc == 0:
                    set_server_status('initialized')
                else:
                    shared_state.task4_log.append(
                        '*** preflight refused: the bench is not ready. '
                        'Fix what it named, then Destroy and Initialize again.')
                    set_server_status('error')
            logger.info('background worker ended')

        t = threading.Thread(target=background_worker)
        t.start()
        set_thread(CMD_ID, t)
    else:
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] Current status is {shared_state.server_status}. reject "{CMD_ID}"')

    return '', 204


class ConfigForm(FlaskForm):
    inspector = StringField("inspector", validators=[InputRequired()])
    moduleSTATUS = StringField("moduleSTATUS", validators=[InputRequired()])
    moduleIDA = StringField("moduleIDA", validators=[OptionalV()])
    moduleIDB = StringField("moduleIDB", validators=[OptionalV()])
    moduleIDC = StringField("moduleIDC", validators=[OptionalV()])
    powerBoardA = StringField("powerBoardA", validators=[OptionalV()])
    powerBoardB = StringField("powerBoardB", validators=[OptionalV()])
    powerBoardC = StringField("powerBoardC", validators=[OptionalV()])
    nRUNS = IntegerField("nRUNS", validators=[InputRequired(), NumberRange(min=1, max=20)])
    # Bring-up retries per slot; optional so an older cached page can still Configure.
    bringupTRIES = IntegerField("bringupTRIES",
                                validators=[OptionalV(), NumberRange(min=1, max=40)])
    label = StringField("label", validators=[InputRequired()])
    skipPROBE = StringField("skipPROBE", validators=[OptionalV()])
    submit = SubmitField("Configure")


@app.route('/submit', methods=['POST','GET'])
def Configure():
    CMD_ID = 'Configure'

    if not check_jobmode(): return '', 204
    if not isCommandRunable(shared_state.server_status, CMD_ID): return '', 204

    json_data = request.get_json()
    if not json_data:
        return jsonify({'status': 'error', 'message': 'Missing JSON data'}), 400

    form = ConfigForm(data=json_data)

    if not form.validate_on_submit():
        errors = {f: m for f, m in form.errors.items()}
        current_app.logger.warning(f'[Configure] Validation errors: {errors}')
        return jsonify({'status': 'error', 'errors': errors}), 400

    ### bench scripts need the 15-character dashless serial (chars 5 and 6 are read by position)
    resolved = {}
    errors = {}
    for S in SLOTS:
        raw = getattr(form, f'moduleID{S}').data or ''
        if not raw.strip():
            CONF_DICT[f'moduleID{S}'] = ''
            continue
        override = (getattr(form, f'powerBoard{S}').data or 'auto').strip().lower()
        try:
            serial, row, power = board_params.params(raw, override)
        except ValueError as e:
            errors[f'moduleID{S}'] = [str(e)]
            continue
        CONF_DICT[f'moduleID{S}'] = serial
        CONF_DICT[f'powerBoard{S}'] = override
        resolved[S] = (serial, board_params.describe(row, power))

    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400
    if not resolved:
        return jsonify({'status': 'error', 'errors': 'No slot has a module serial.'}), 400

    CONF_DICT['inspector'] = str(form.inspector.data)
    CONF_DICT['moduleSTATUS'] = str(form.moduleSTATUS.data)
    CONF_DICT['nRUNS'] = str(form.nRUNS.data)
    CONF_DICT['bringupTRIES'] = str(form.bringupTRIES.data or 4)
    CONF_DICT['label'] = re.sub(r'[^A-Za-z0-9_-]+', '', str(form.label.data)) or 'ped'
    CONF_DICT['skipPROBE'] = '1' if str(form.skipPROBE.data) in ('1', 'True', 'true', 'on') else '0'

    ### show the power decision before Run: a wrong flag reads as "no ROCs".
    lines = [f'  {S}: {serial}   {desc}' for S, (serial, desc) in sorted(resolved.items())]
    mesg = ('Multi Pedestal Run configured\n\n'
            + '\n'.join(lines)
            + f"\n\n  {CONF_DICT['nRUNS']} pedestals per slot, label '{CONF_DICT['label']}'"
            + f", probe {'skipped' if CONF_DICT['skipPROBE'] == '1' else 'RUN (costs a bring-up)'}"
            + f", up to {CONF_DICT['bringupTRIES']} bring-up tries per slot"
            + '\n\n  Slots run one at a time, in the order shown.'
            + '\n  Check the power column before pressing Run.')

    shared_state.task4_slots.clear()
    for S in sorted(resolved):
        d = _slot(S)
        d['params'] = resolved[S][1]

    current_app.logger.info(f'[Configure] CONF_DICT: {CONF_DICT}')
    set_server_status('configured')
    return jsonify({'status': 'success', 'message': mesg}), 200


@app.route('/run', methods=['POST'])
def Run():
    ''' run bash command `make run` at background '''
    CMD_ID = 'Run'
    if not check_jobmode(): return '', 204

    job_stop_flags[CMD_ID].clear()
    if isCommandRunable(shared_state.server_status, CMD_ID):
        set_server_status('running')
        shared_state.task4_log.clear()
        for S in list(shared_state.task4_slots):
            _set(S, 'queued', 'queued')

        def background_worker():
            try:
                command = ExecCMD(CMD_ID, CONF_DICT)
                run_command(command, CMD_ID)
            finally:
                set_server_status('idle')
            logger.info('background worker ended')

        t = threading.Thread(target=background_worker)
        t.start()
        set_thread(CMD_ID, t)
    else:
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] Current status is {shared_state.server_status}. reject "{CMD_ID}"')

    return '', 204


@app.route('/stop', methods=['POST'])
def Stop():
    if not check_jobmode(): return '', 204
    CMD_ID = 'Stop'

    set_server_status('stopping')
    job_stop_flags['Run'].set()

    ### local make only; makefile_task4's stop target reaches the client host and Kria.
    kill_local_make()
    if job_thread['Run'] and job_thread['Run'].is_alive():
        job_thread['Run'].join()

    job_stop_flags['Run'].clear()

    def background_worker():
        try:
            command = ExecCMD(CMD_ID, CONF_DICT)
            run_command(command, CMD_ID)
        finally:
            set_server_status('idle')

    t = threading.Thread(target=background_worker)
    t.start()
    t.join()

    for S, d in list(shared_state.task4_slots.items()):
        if d['state'] not in ('done', 'failed', 'queued'):
            _set(S, 'failed', 'stopped by operator')

    set_server_status('stopped')
    return '', 204


@app.route('/destroy', methods=['POST'])
def Destroy():
    if not check_jobmode(): return '', 204
    CMD_ID = 'Destroy'

    if isCommandRunable(shared_state.server_status, CMD_ID):
        set_server_status('destroying')
        for name, flag in job_stop_flags.items(): flag.set()
        kill_local_make()

        for name, t in job_thread.items():
            if t and t.is_alive():
                t.join()

        for name, flag in job_stop_flags.items(): flag.clear()

        def background_worker():
            try:
                command = ExecCMD(CMD_ID, CONF_DICT)
                run_command(command, CMD_ID)
            finally:
                logger.info("Destroy ended")

        t = threading.Thread(target=background_worker)
        t.start()
        t.join()

        set_server_status('destroyed')
    else:
        current_app.logger.debug(f'[ServerAction][{CMD_ID}] Current status is {shared_state.server_status}. reject "{CMD_ID}"')
    return '', 204


@app.route('/status')
def status():
    hasupdate = False

    last_modified = os.path.getmtime(dirDAQresult) if os.path.isdir(dirDAQresult) else ''
    if last_modified != shared_state.DAQresult_current_modified:
        hasupdate = True
        shared_state.DAQresult_current_modified = last_modified

    daq_result_dirs = [subdir for subdir in os.listdir(dirDAQresult)
                       if os.path.isdir(f'{dirDAQresult}/{subdir}')] if hasupdate else []
    ### copies: the run thread mutates the live containers while this serializes.
    return jsonify({'status': shared_state.server_status,
                    'jobmode': shared_state.jobmode,
                    'kria': shared_state.kria_ip,
                    'DAQres': daq_result_dirs,
                    'slots': {s: dict(d) for s, d in list(shared_state.task4_slots.items())},
                    'log': list(shared_state.task4_log)[-40:]})


@app.route('/board_table')
def board_table():
    '''The serial -> parameters table, so the form can label a serial as it is typed.'''
    return jsonify(board_params.TABLE)


@app.route('/main.html')
def main():
    daq_result_dirs = [subdir for subdir in os.listdir(dirDAQresult)
                       if os.path.isdir(f'{dirDAQresult}/{subdir}')] if os.path.isdir(dirDAQresult) else []
    return render_template('index_task4.html', DAQres=daq_result_dirs,
                           inspectors=DEFAULT_INSPECTORS, slots=SLOTS,
                           krias=kria_select.KRIAS, kria=shared_state.kria_ip,
                           defaults=CONF_DICT)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='[basicCONFIG] %(levelname)s - %(message)s',
                        datefmt='%H:%M:%S')
    app_main = Flask(__name__)
    app_main.register_blueprint(app, url_prefix='/task4')
    app_main.config["SECRET_KEY"] = '7eCZ^6nUxb6hjN5EbLYak&fvt'
    csrf = CSRFProtect(app_main)

    @app_main.route("/")
    def index():
        return render_template("index_task4.html")
    app_main.run(debug=True)
