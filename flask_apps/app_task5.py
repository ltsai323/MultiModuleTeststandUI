import json
import logging
import os
import re
import sys
import time

import yaml
from flask import Flask, render_template, request, jsonify, Blueprint, abort, Response
from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms.validators import InputRequired, Optional as OptionalV, NumberRange
from wtforms import StringField, SubmitField, IntegerField, FloatField

import flask_apps.shared_state as shared_state
import flask_apps.lanes as lanes_mod
from PythonTools.server_status import isCommandRunable

### Multi Pedestal Run with optional HV bias scan; up to 8 Krias, one lane each.
JOBMODE = 'task5'

### serial -> bring-up parameter table, shared with the bench scripts
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'task4_mmts_pedestal'))
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
KEITHLEY = {}
_conf = {}
try:
    with open(MMTS_CONF, 'r') as fIN:
        _conf = yaml.safe_load(fIN) or {}
        BENCH = _conf.get('MMTS_bench', {}) or {}
        KEITHLEY = (_conf.get('MMTS_hardwares', {}) or {}).get('keithley', {}) or {}
except FileNotFoundError:
    pass
SLOTS = [str(s) for s in BENCH.get('slots', ['A', 'B', 'C'])]
HV = BENCH.get('hv', {}) or {}
PARALLEL = str(HV.get('parallel_bias', False)).lower() in ('1', 'true', 'yes')
### Vitrek relay per tray position ("3C" -> 8). A lane is a row, its slots L/C/R.
CHANNELS = {}
for _pos, _c in (_conf.get('MMTS_channel_config') or {}).items():
    try:
        CHANNELS[str(_pos)] = int((_c or {}).get('HVchannel'))
    except (TypeError, ValueError):
        pass
SLOT_POS = {'A': 'L', 'B': 'C', 'C': 'R'}
### The lock hv_lock.sh takes for the Keithley; the page shows who holds it.
HV_LOCK = os.environ.get('MMTS_HV_SESSION_LOCK', os.path.join(ROOT, 'logs', 'hv_session.lock'))
### The instrument's ceiling. board_params caps each geometry further (LD 600).
HVMAX = int(KEITHLEY.get('MaxVoltage', 800))
### [(host, name)]: the host reaches the bench, the name is what the page shows
KRIAS = lanes_mod.parse_krias(BENCH)

DEFAULTS = {
        'inspector': '',
        'moduleSTATUS': 'Bolted',   ### every module on this bench is bolted
        'moduleIDA': '', 'moduleIDB': '', 'moduleIDC': '',
        'powerBoardA': 'auto', 'powerBoardB': 'auto', 'powerBoardC': 'auto',
        'nRUNS': str(BENCH.get('default_nruns', 5)),
        'label': str(BENCH.get('default_label', 'ped')),
        'skipPROBE': str(BENCH.get('skip_probe', 1)),
        'bringupTRIES': str(BENCH.get('bringup_tries', 4)),
        'biasVOLTS': '1,10,50,100,300,300,500',
        'hvSwitch': str(HV.get('switch', 'none')),
        'trimPEDS': '0' if str(HV.get('trim_pedestals', True)).lower() in ('0', 'false', 'no') else '1',
        'leakCHECK': '0' if str(HV.get('leak_check', True)).lower() in ('0', 'false', 'no') else '1',
        'useHV': '0',
        'temperature': '', 'humidity': '',
        }
### The leakage abort is the config's, no longer a form field.
MAXLEAK = str(HV.get('leak_abort_uA', 1000))
### Last temperature and humidity typed in, so a page reload keeps them.
LAST_COND = os.path.join(ROOT, 'logs', 'last_conditions.json')


def last_conditions():
    try:
        with open(LAST_COND) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}

BENCH_KEYS = ['moduleIDA', 'moduleIDB', 'moduleIDC',
              'powerBoardA', 'powerBoardB', 'powerBoardC',
              'nRUNS', 'label', 'skipPROBE', 'bringupTRIES',
              'biasVOLTS', 'hvSwitch', 'maxLEAK', 'useHV', 'trimPEDS', 'leakCHECK', 'temperature', 'humidity']

logger = logging.getLogger('werkzeug')

app = Blueprint('app_task5', __name__)

LANES = lanes_mod.load_lanes(BENCH, ROOT)
BY_NAME = {l.name: l for l in LANES}


def update_aggregate():
    """Aggregate status for the rest of the GUI (job mode switch needs every lane free)."""
    st = [l.status for l in LANES]
    if all(s in lanes_mod.FREE for s in st):
        shared_state.server_status = 'destroyed' if 'destroyed' in st else 'startup'
    elif any(s in lanes_mod.BUSY for s in st):
        shared_state.server_status = 'running'
    else:
        shared_state.server_status = 'idle'


for _l in LANES:
    _l.conf = dict(DEFAULTS)
    _l.on_status = update_aggregate


def parse_bias(text, cap=None):
    """'1, 10,300' -> [1, 10, 300]. Raises ValueError on anything else.

    Same check as run_slots_hv.sh: catch a bad voltage before it reaches the Keithley.
    """
    out = []
    for tok in str(text or '').replace(' ', '').split(','):
        if not tok:
            continue
        if not tok.isdigit():
            raise ValueError(f'"{tok}" is not a whole number of volts')
        v = int(tok)
        if cap is not None and v > cap:
            raise ValueError(f'{v} V is above the limit of {cap} V')
        out.append(v)
    if not out:
        raise ValueError('give at least one bias voltage')
    return out


def ExecCMD(lane, jobID):
    ### debug_mode prints each command instead of running it (no bench needed).
    make = 'make -n' if shared_state.debug_mode else 'make'
    hv = '1' if lane.use_hv else '0'
    if jobID == 'Init':
        ### plain preflight: an HV run checks the Keithley itself before powering anything
        return f'{make} -f makefile_task5 initialize useHV=0 JobName=Init'
    if jobID == 'Run':
        lane.runidx += 1
        ### unique across GUI restarts: names the gallery folder and log file
        lane.runtag = f'{lane.name}_{time.strftime("%Y%m%d_%H%M%S")}'
        opts = ' '.join(f"{k}='{v}'" for k, v in lane.conf.items()
                        if k in BENCH_KEYS and v != '')
        ### never -j: one Kria, one i2c-server, one daq-server, one trigger claim
        return f'{make} -f makefile_task5 run JobName=Run runTAG={lane.runtag} {opts}'
    sw = lane.conf.get('hvSwitch') or 'none'
    if jobID == 'Stop':
        return f'{make} -f makefile_task5 stop useHV={hv} hvSwitch={sw} JobName=Stop'
    if jobID == 'Destroy':
        return f'{make} -f makefile_task5 destroy useHV={hv} hvSwitch={sw} JobName=Destroy'


def check_jobmode() -> bool:
    if not shared_state.jobmode:
        logger.info(f'[ReplaceJobMode] jobmode modified from None to {JOBMODE}')
        shared_state.jobmode = JOBMODE
        return True
    if shared_state.jobmode == JOBMODE:
        return True
    logger.warning(f'[InvalidJobMode] jobmode "{shared_state.jobmode}" mismatched with local "{JOBMODE}". Ignore command')
    return False


def relay_of(lane, slot):
    """(position, Vitrek relay) for a slot of a lane, or (position, None)."""
    pos = f'{lane.hv_row}{SLOT_POS[slot]}'
    return pos, CHANNELS.get(pos)


def keithley_owner():
    """'K2 B' while a live run holds the Keithley, else ''."""
    try:
        with open(os.path.join(HV_LOCK, 'owner')) as f:
            parts = f.read().split()
        os.kill(int(parts[2]), 0)
        return ' '.join(parts[:2])
    except PermissionError:
        return ' '.join(parts[:2])
    except (OSError, IndexError, ValueError):
        return ''


def lane_or_404(name):
    lane = BY_NAME.get(name)
    if lane is None:
        return None, (jsonify({'status': 'error', 'message': f'no lane {name}'}), 404)
    return lane, None


def refuse(msg, code=409):
    return jsonify({'status': 'error', 'message': lanes_mod.shelf(msg)}), code


# --------------------------------------------------------------------------
# Lane actions
# --------------------------------------------------------------------------
@app.route('/lane/<name>/init', methods=['POST'])
def Init(name):
    lane, err = lane_or_404(name)
    if err: return err
    if not check_jobmode(): return '', 204
    if not isCommandRunable(lane.status, 'Init'):
        return refuse(f'{name} is {lane.status}; Clear it first')

    kria = str((request.get_json(silent=True) or {}).get('kria', lane.kria) or '').strip()
    if not lanes_mod.valid_host(kria):
        return refuse(f'{name}: "{kria}" is not a hostname or an IP address', 400)
    ### one puller per Kria: two lanes on one Kria would steal each other's stream
    for other in LANES:
        if other is not lane and other.kria == kria and other.status not in lanes_mod.FREE:
            return refuse(f'{kria} is already driven by {other.name}')
    lane.kria = kria
    lane.use_hv = False
    lane.stop_flag.clear()
    lane.reset_progress()
    lane.set_status('initializing')

    def worker():
        rc = 1
        try:
            rc = lane.run_command(ExecCMD(lane, 'Init'), logger)
        finally:
            shared_state.DAQresult_current_modified = ''
            ### a refused preflight must not arm Run
            if rc == 0:
                lane.set_status('initialized')
            else:
                lane.log.append('*** preflight refused: this Kria is not ready. '
                                'Fix what it named, then Clear and Initialize again.')
                lane.set_status('error')

    lane.start('Init', worker)
    return '', 204


class ConfigForm(FlaskForm):
    inspector = StringField("inspector", validators=[InputRequired()])
    moduleSTATUS = StringField("moduleSTATUS", validators=[OptionalV()])
    moduleIDA = StringField("moduleIDA", validators=[OptionalV()])
    moduleIDB = StringField("moduleIDB", validators=[OptionalV()])
    moduleIDC = StringField("moduleIDC", validators=[OptionalV()])
    powerBoardA = StringField("powerBoardA", validators=[OptionalV()])
    powerBoardB = StringField("powerBoardB", validators=[OptionalV()])
    powerBoardC = StringField("powerBoardC", validators=[OptionalV()])
    nRUNS = IntegerField("nRUNS", validators=[InputRequired(), NumberRange(min=1, max=20)])
    bringupTRIES = IntegerField("bringupTRIES",
                                validators=[OptionalV(), NumberRange(min=1, max=40)])
    label = StringField("label", validators=[InputRequired()])
    skipPROBE = StringField("skipPROBE", validators=[OptionalV()])
    useHV = StringField("useHV", validators=[OptionalV()])
    biasVOLTS = StringField("biasVOLTS", validators=[OptionalV()])
    hvSwitch = StringField("hvSwitch", validators=[OptionalV()])
    trimPEDS = StringField("trimPEDS", validators=[OptionalV()])
    leakCHECK = StringField("leakCHECK", validators=[OptionalV()])
    temperature = FloatField("temperature", validators=[OptionalV(), NumberRange(min=-40, max=80)])
    humidity = FloatField("humidity", validators=[OptionalV(), NumberRange(min=0, max=100)])
    submit = SubmitField("Configure")


@app.route('/lane/<name>/submit', methods=['POST'])
def Configure(name):
    lane, err = lane_or_404(name)
    if err: return err
    if not check_jobmode(): return '', 204
    if not isCommandRunable(lane.status, 'Configure'):
        return refuse(f'{name} is {lane.status}; Initialize it first')

    json_data = request.get_json()
    if not json_data:
        return jsonify({'status': 'error', 'message': 'Missing JSON data'}), 400
    form = ConfigForm(data=json_data)
    if not form.validate_on_submit():
        return jsonify({'status': 'error', 'errors': dict(form.errors)}), 400

    use_hv = str(form.useHV.data or '0') in ('1', 'True', 'true', 'on')

    ### bench scripts need the 15-character dashless serial (chars 5 and 6 are read by position)
    conf = dict(lane.conf)
    resolved = {}
    errors = {}
    for S in SLOTS:
        raw = getattr(form, f'moduleID{S}').data or ''
        if not raw.strip():
            conf[f'moduleID{S}'] = ''
            continue
        override = (getattr(form, f'powerBoard{S}').data or 'auto').strip().lower()
        try:
            serial, row, power = board_params.params(raw, override)
        except ValueError as e:
            errors[f'moduleID{S}'] = [str(e)]
            continue
        conf[f'moduleID{S}'] = serial
        conf[f'powerBoard{S}'] = override
        resolved[S] = (serial, board_params.describe(row, power), row)

    bias = []
    switch = (form.hvSwitch.data or 'none').strip().lower()
    if use_hv:
        if switch not in ('none', 'vitrek'):
            errors['hvSwitch'] = ['must be none or vitrek']
        others = [o for o in LANES
                  if o is not lane and o.use_hv and o.status not in lanes_mod.FREE]
        if switch == 'none':
            ### One Keithley, one cable moved by hand: one lane with HV at a time.
            for o in others:
                errors['useHV'] = [f'{o.name} already has HV on, and the HV cable is moved by hand; '
                                   'with one cable only one Kria can have HV (or use the Vitrek)']
        else:
            ### Vitrek: lanes share the Keithley; all must use the Vitrek, each its own relay row.
            for o in others:
                if (o.conf.get('hvSwitch') or 'none') != 'vitrek':
                    errors['useHV'] = [f'{o.name} has HV on through the cable; finish or Clear it first']
                elif o.hv_row == lane.hv_row:
                    errors['useHV'] = [f'{o.name} uses the same Vitrek row {lane.hv_row}']
            for S in resolved:
                pos, relay = relay_of(lane, S)
                if relay is None:
                    errors[f'moduleID{S}'] = [f'no Vitrek relay for tray position {pos} '
                                              '(MMTS_channel_config)']
        ### check the bias list against both ceilings before Run is armed
        try:
            bias = parse_bias(form.biasVOLTS.data, HVMAX)
            for S, (_serial, _desc, row) in resolved.items():
                cap = min(int(row['maxv']), HVMAX)
                over = [v for v in bias if v > cap]
                if over:
                    errors['biasVOLTS'] = [f'slot {S} ({row["name"]}) takes at most {cap} V, '
                                           f'and the list asks for {over[0]} V']
        except ValueError as e:
            errors['biasVOLTS'] = [str(e)]

    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400
    if not resolved:
        return jsonify({'status': 'error', 'errors': f'{lane.label}: no slot has a module serial.'}), 400

    conf['inspector'] = str(form.inspector.data)
    conf['moduleSTATUS'] = str(form.moduleSTATUS.data or DEFAULTS['moduleSTATUS'])
    conf['nRUNS'] = str(form.nRUNS.data)
    conf['bringupTRIES'] = str(form.bringupTRIES.data or 4)
    conf['label'] = re.sub(r'[^A-Za-z0-9_-]+', '', str(form.label.data)) or 'ped'
    conf['skipPROBE'] = '1' if str(form.skipPROBE.data) in ('1', 'True', 'true', 'on') else '0'
    conf['useHV'] = '1' if use_hv else '0'
    t, rh = form.temperature.data, form.humidity.data
    conf['temperature'] = '' if t is None else f'{t:g}'
    conf['humidity'] = '' if rh is None else f'{rh:g}'
    try:
        with open(LAST_COND, 'w') as f:
            json.dump({'temperature': conf['temperature'], 'humidity': conf['humidity'],
                       'at': time.strftime('%Y-%m-%d %H:%M')}, f)
    except OSError:
        pass
    if use_hv:
        conf['biasVOLTS'] = ','.join(str(v) for v in bias)
        conf['hvSwitch'] = switch
        ### not sent (an old page, a script) = the config's default
        t = str(form.trimPEDS.data or DEFAULTS['trimPEDS'])
        conf['trimPEDS'] = '1' if t in ('1', 'True', 'true', 'on') else '0'
        k = str(form.leakCHECK.data or DEFAULTS['leakCHECK'])
        conf['leakCHECK'] = '1' if k in ('1', 'True', 'true', 'on') else '0'
        conf['maxLEAK'] = MAXLEAK
    lane.conf = conf
    lane.use_hv = use_hv

    ### show the power decision and the bias plan before Run, so nobody biases the wrong bench
    lines = [f'  {S}: {serial}   {desc}' for S, (serial, desc, _row) in sorted(resolved.items())]
    probe = 'skipped' if conf['skipPROBE'] == '1' else 'RUN (costs a bring-up; no other Kria may run meanwhile)'
    if use_hv:
        if switch == 'none':
            routing = 'one HV cable, moved by hand: the job pauses and asks before each slot'
        else:
            relays = ', '.join(f'{S} relay {relay_of(lane, S)[1]} ({relay_of(lane, S)[0]})'
                               for S in sorted(resolved))
            routing = (f'Vitrek 964i: {relays}. The Keithley is shared: each slot waits '
                       'its turn after its gate, the other Krias keep running')
        plan = (f"\n\n  HV ON: bias points {', '.join(str(v) for v in bias)} V"
                + (f"\n  TRIMMING at {min(int(HV.get('trim_volts') or 300), max(bias))} V first: one untrimmed reference "
                   "pedestal, pedestal_scan, vrefnoinv_scan, vrefinv_scan; then every bias point trimmed "
                   f"(label '{conf['label']}_trimmed')" if conf['trimPEDS'] == '1' else "\n  no trimming")
                + f"\n  {conf['nRUNS']} pedestals per bias point, label '{conf['label']}'"
                + (f"\n  leakage check aborts a slot above {conf['maxLEAK']} uA below 500 V"
                   if conf['leakCHECK'] == '1' else
                   "\n  NO LEAKAGE CHECK: a short or a leaky sensor is not caught; "
                   "only the Keithley compliance protects the modules")
                + f"\n  HV routing: {routing}")
        warn = '\n  Check the power column, and check which bench the HV cable is on.'
    else:
        plan = (f"\n\n  HV off: the Keithley is not touched"
                f"\n  {conf['nRUNS']} pedestals per slot, label '{conf['label']}'")
        warn = '\n  Check the power column before pressing Run.'
    cond = (f"\n  conditions: {conf['temperature'] or '?'} C, {conf['humidity'] or '?'} %RH"
            + ('' if conf['temperature'] and conf['humidity'] else '   (not entered)'))
    mesg = (f'{lane.label} ({lane.kria}) configured\n\n' + '\n'.join(lines) + plan + cond
            + f"\n  probe {probe}, up to {conf['bringupTRIES']} bring-up tries per slot"
            + '\n\n  Slots run one at a time, in the order shown.' + warn)

    lane.slots.clear()
    for S in sorted(resolved):
        lane.slot(S)['params'] = resolved[S][1]

    current_app.logger.info(f'[Configure][{name}] {conf}')
    lane.set_status('configured')
    return jsonify({'status': 'success', 'message': mesg}), 200


@app.route('/lane/<name>/run', methods=['POST'])
def Run(name):
    lane, err = lane_or_404(name)
    if err: return err
    if not check_jobmode(): return '', 204
    if not isCommandRunable(lane.status, 'Run'):
        return refuse(f'{name} is {lane.status}; Configure it first')

    ### the 12+12 probe writes the shared <FAMILY>_mux<S>_ped.yaml, so it runs alone
    running = [l for l in LANES if l is not lane and l.status == 'running']
    if lane.conf.get('skipPROBE') == '0' and running:
        return refuse(f'{name} asks for the 12+12 probe, which runs alone; '
                      f'{", ".join(l.name for l in running)} running')
    probing = [l.name for l in running if l.conf.get('skipPROBE') == '0']
    if probing:
        return refuse(f'{", ".join(probing)} is running the 12+12 probe; wait for it')

    lane.stop_flag.clear()
    lane.log.clear()
    lane.clear_pause()      ### a pause file left by a killed run would release this one
    for S in list(lane.slots):
        lane.set_slot(S, 'queued', 'queued')
    lane.set_status('running')
    cmd = ExecCMD(lane, 'Run')
    ### the run's record next to its log: who, what, when, and the room conditions
    try:
        os.makedirs(lane.pause_dir, exist_ok=True)
        with open(os.path.join(lane.pause_dir, lane.runtag + '.json'), 'w') as f:
            json.dump({'runtag': lane.runtag, 'lane': lane.name, 'kria': lane.kria,
                       'start': time.strftime('%Y-%m-%dT%H:%M:%S'), 'use_hv': lane.use_hv,
                       'conf': lane.conf}, f, indent=1)
    except OSError as e:
        lane.log.append(f'*** could not write the run record: {e}')

    def worker():
        try:
            lane.run_command(cmd, logger)
        finally:
            if lane.status == 'running':
                lane.set_status('idle')

    lane.start('Run', worker)
    return '', 204


@app.route('/lane/<name>/continue', methods=['POST'])
def Continue(name):
    '''Release the "move the HV cable" pause. Safe when nothing is waiting.'''
    lane, err = lane_or_404(name)
    if err: return err
    if not check_jobmode(): return '', 204
    if not lane.read_pause():
        return refuse('nothing is waiting', 400)
    os.makedirs(lane.pause_dir, exist_ok=True)
    open(lane.continue_file, 'w').close()
    current_app.logger.info(f'[Continue][{name}] HV cable pause released')
    return jsonify({'status': 'success'}), 200


@app.route('/lane/<name>/stop', methods=['POST'])
def Stop(name):
    lane, err = lane_or_404(name)
    if err: return err
    if not check_jobmode(): return '', 204

    lane.set_status('stopping')
    ### local make only; makefile_task5's stop reaches the client, Kria and Keithley.
    lane.stop_flag.set()
    lane.kill_group()
    lane.end_client_session()   # a hung scan holds the run's output open
    lane.join('Run')
    lane.stop_flag.clear()
    lane.run_command(ExecCMD(lane, 'Stop'), logger)

    for S, d in list(lane.slots.items()):
        if d['state'] not in ('done', 'failed', 'queued'):
            lane.set_slot(S, 'failed', 'stopped by operator')
    lane.set_status('stopped')
    return '', 204


@app.route('/lane/<name>/clear', methods=['POST'])
def Clear(name):
    '''Stop, payload power off, HV off, this lane's puller gone: back to the start.'''
    lane, err = lane_or_404(name)
    if err: return err
    if not check_jobmode(): return '', 204
    if not isCommandRunable(lane.status, 'Destroy'):
        return refuse(f'{name} is {lane.status}; nothing to clear')

    lane.set_status('destroying')
    lane.stop_flag.set()
    lane.kill_group()
    lane.end_client_session()   # a hung scan holds the run's output open
    for kind in ('Init', 'Run'):
        lane.join(kind)
    lane.stop_flag.clear()
    lane.run_command(ExecCMD(lane, 'Destroy'), logger)
    lane.use_hv = False
    # blank page pane; the log files on disk stay
    lane.reset_progress()
    lane.logfile = ''
    lane.set_status('destroyed')
    return '', 204


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
def result_dirs():
    if not os.path.isdir(dirDAQresult):
        return []
    return sorted(d for d in os.listdir(dirDAQresult)
                  if os.path.isdir(os.path.join(dirDAQresult, d)))


@app.route('/status')
def status():
    ### always the whole list, so every open page sees a new run
    return jsonify({'status': shared_state.server_status,
                    'jobmode': shared_state.jobmode,
                    'DAQres': result_dirs(),
                    'keithley': keithley_owner(),
                    'lanes': [l.snapshot() for l in LANES]})


@app.route('/board_table')
def board_table():
    '''The serial -> parameters table, so the form can label a serial as it is typed.'''
    return jsonify(board_params.TABLE)


@app.route('/main.html')
def main():
    defaults = dict(DEFAULTS)
    last = last_conditions()
    defaults['temperature'] = last.get('temperature', '')
    defaults['humidity'] = last.get('humidity', '')
    return render_template('index_task5.html', DAQres=result_dirs(),
                           inspectors=DEFAULT_INSPECTORS, slots=SLOTS,
                           lanes=LANES, krias=KRIAS, hvmax=HVMAX, defaults=defaults,
                           cond_at=last.get('at', ''), maxleak=MAXLEAK, channels=CHANNELS,
                           parallel=PARALLEL)


# --------------------------------------------------------------------------
# Full log files: the page pane holds only the tail
# --------------------------------------------------------------------------
_LOGNAME = re.compile(r'^[KS]\d_[A-Za-z0-9_]+\.log$')


def lane_logs(lane):
    try:
        names = [n for n in os.listdir(lane.pause_dir) if _LOGNAME.match(n)]
    except OSError:
        return []
    return sorted(names, key=lambda n: os.path.getmtime(os.path.join(lane.pause_dir, n)), reverse=True)


@app.route('/lane/<name>/log')
def log_page(name):
    lane, err = lane_or_404(name)
    if err: return err
    files = lane_logs(lane)
    pick = request.args.get('f') or (os.path.basename(lane.logfile) if lane.logfile else '') \
        or (files[0] if files else '')
    if pick and pick not in files:
        abort(404)
    return render_template('log_task5.html', lane=lane, files=files, pick=pick,
                           path=os.path.join(lane.pause_dir, pick) if pick else '')


@app.route('/lane/<name>/log.txt')
def log_text(name):
    lane, err = lane_or_404(name)
    if err: return err
    pick = request.args.get('f', '')
    if pick not in lane_logs(lane):
        abort(404)
    with open(os.path.join(lane.pause_dir, pick), errors='replace') as f:
        body = f.read()
    return Response(body, mimetype='text/plain; charset=utf-8',
                    headers={'X-Lane-Busy': '1' if lane.busy() else '0'})


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='[basicCONFIG] %(levelname)s - %(message)s',
                        datefmt='%H:%M:%S')
    app_main = Flask(__name__)
    app_main.register_blueprint(app, url_prefix='/task5')
    app_main.config["SECRET_KEY"] = '7eCZ^6nUxb6hjN5EbLYak&fvt'
    csrf = CSRFProtect(app_main)
    app_main.run(debug=True)
