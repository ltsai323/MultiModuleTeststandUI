"""Up to 8 Krias driven side by side from one page: one Lane per Kria.

Each lane runs makefile_task5 with its own MMTS_LANE, MMTS_KRIA_IP,
MMTS_PULLER_PORT, MMTS_REGISTRY_NAME and MMTS_HV_ROW (see Lane.env).
Within a lane the slots run one at a time. Plan: docs/plan_multi_kria_lanes.md.
"""
import json
import os
import re
import signal
import subprocess
import threading
import time
from collections import deque

MAX_LANES = 8
BASE_PORT = 6100            ### lane i gets 6100 + i: clear of 6001 and of 6002..6025

### Progress comes only from stage banners, run_slot.sh exit codes and hv.py "HV <cmd> ..." lines.
LED = {
    'queued': 'gray', 'starting': 'yellow', 'bringup': 'yellow', 'up': 'yellow',
    'gate': 'yellow', 'gated': 'yellow', 'hv': 'yellow', 'hv-wait': 'yellow', 'pedestal': 'green',
    'done': 'green', 'failed': 'red', 'gate-failed': 'red', 'leak-abort': 'red', 'left-out': 'red',
}

### With HV, run_slot.sh does bring-up and gate only (exit 0 = ready for bias).
EXIT_REASON_HV = {
    '0': 'gate passed', '1': 'bring-up failed', '2': 'probe gave no summary',
    '3': 'registry or link map refused', '4': 'gate failed, no HV applied',
    '5': 'first pedestal stalled, no HV applied',
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
_HVLINE = re.compile(r'^HV (\w+) (ok|abort|fail)\s*(\{.*\})?\s*$')
_HOST = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$')

BUSY = ('initializing', 'running', 'stopping', 'destroying')
FREE = ('startup', 'destroyed')


def valid_host(host: str) -> bool:
    return bool(_HOST.match(host or ''))


def shelf(text):
    """Display only: lane S8 (or K8) reads "Shelf 8"; ids, dirs and run tags keep S8."""
    return re.sub(r'\b[KS]([1-9])\b', r'Shelf \1', str(text))


class Lane:
    @property
    def label(self):
        return shelf(self.name)

    def __init__(self, name, kria='', port=None, root='.', hv_row=None):
        self.name = name
        self.kria = kria
        self.port = int(port)
        digits = re.sub(r'\D', '', name)
        self.hv_row = int(hv_row) if hv_row else int(digits or 0)
        self.status = 'startup'
        self.conf = {}
        self.use_hv = False
        self.runidx = 0
        self.runtag = ''
        self.slots = {}
        self.log = deque(maxlen=2000)
        self.logfile = ''        ### full log of the last command, on disk
        self.proc = None
        self.stop_flag = threading.Event()
        self.threads = {'Init': None, 'Run': None, 'Stop': None, 'Destroy': None}
        self.pause_dir = os.path.join(root, 'logs', 'lanes', name)
        self.on_status = None   ### set by the app: recompute the aggregate status

    # --- identity on the bench ---------------------------------------------
    def registry_name(self):
        return 'module_ids_' + re.sub(r'[^A-Za-z0-9.-]+', '_', self.kria) + '.json'

    def env(self):
        """The variables that keep this lane apart from the others."""
        return {
            'MMTS_LANE': self.name,
            'MMTS_KRIA_IP': self.kria,
            'MMTS_PULLER_PORT': str(self.port),
            'MMTS_REGISTRY_NAME': self.registry_name(),
            'MMTS_PAUSE_DIR': self.pause_dir,
            'MMTS_HV_ROW': str(self.hv_row),
        }

    def set_status(self, s):
        self.status = s
        if self.on_status:
            self.on_status()

    def busy(self):
        return self.status in BUSY

    # --- progress -------------------------------------------------------------
    def reset_progress(self):
        self.slots.clear()
        self.log.clear()

    def slot(self, s):
        return self.slots.setdefault(
            s, {'slot': s, 'state': 'queued', 'led': LED['queued'], 'stage': 'queued',
                'params': '', 'peds': 0, 'nruns': 0, 'exit': None,
                'bv': None, 'leak_uA': None, 'points': 0})

    def set_slot(self, s, state, stage):
        d = self.slot(s)
        d['state'] = state
        d['led'] = LED.get(state, 'gray')
        d['stage'] = shelf(stage)
        return d

    def parse_progress(self, line, current=None):
        """Fold one output line into self.slots. Returns the slot in play.

        `current` is the slot of the last banner; most other lines do not name one.
        """
        line = line.rstrip('\n')
        self.log.append(line)

        m = _BANNER.match(line)
        if m:
            s, rest = m.group(1), m.group(2)
            low = rest.lower()
            if low.startswith('params'):
                d = self.set_slot(s, 'starting', 'starting')
                d['params'] = rest[len('params'):].strip()
            elif low.startswith('hv routing'):
                self.set_slot(s, 'hv' if 'vitrek' in low else 'starting', 'routing the HV')
            elif low.startswith('waiting for the keithley') or low.startswith('waiting for the other shelves'):
                self.set_slot(s, 'hv-wait', rest)
            elif low.startswith('bring-up') or low.startswith('second bring-up'):
                self.set_slot(s, 'bringup', 'bring-up')
            elif low.startswith('bringup failed') or low.startswith('second bringup failed'):
                self.set_slot(s, 'failed', 'bring-up failed')
            elif low.startswith('gate'):
                self.set_slot(s, 'gate', 'delay scan gate')
            elif low.startswith('12+12 probe'):
                self.set_slot(s, 'bringup', '12+12 probe')
            elif low.startswith('hv on'):
                self.set_slot(s, 'hv', 'HV on')
            elif low.startswith('trimming failed'):
                self.set_slot(s, 'hv', 'TRIMMING FAILED: the bias scan runs untrimmed')
            elif low.startswith('trimming'):
                self.set_slot(s, 'pedestal', 'trimming (pedestal_scan, vref scans)')
            elif low.startswith('trimmed'):
                d = self.set_slot(s, 'hv', 'trimmed')
                d['trimmed'] = True
            elif low.startswith('leakage check failed'):
                self.set_slot(s, 'failed', 'leakage check failed, no pedestals')
            elif low.startswith('left out'):
                ### parallel bias: the round's summed leakage was over budget
                self.set_slot(s, 'left-out', 'LEFT OUT of the parallel bias (summed leakage over budget), '
                              'no pedestals: check this module by hand')
            elif low.startswith('leakage check'):
                self.set_slot(s, 'hv', 'leakage check')
            elif low.startswith('leakage abort'):
                self.set_slot(s, 'leak-abort', 'leakage abort, no pedestals')
            elif low.startswith('bv '):
                n = re.search(r'bv (\d+)', low)
                d = self.set_slot(s, 'hv', f'ramping to {n.group(1)} V' if n else 'ramping')
                if n:
                    d['bv'] = int(n.group(1))
            elif low.startswith('pedestal '):
                n = re.search(r'pedestal (\d+) of (\d+)', low)
                if n:
                    d = self.set_slot(s, 'pedestal', f'pedestal {n.group(1)}/{n.group(2)}')
                    d['nruns'] = int(n.group(2))
            elif low.startswith('pedestals '):
                n = re.search(r'pedestals \d+\.\.(\d+)', low)
                bv = self.slot(s)['bv']
                d = self.set_slot(s, 'pedestal', 'pedestals running'
                                  + (f' at {bv} V' if bv is not None else ''))
                ### with HV the counter restarts at every bias point
                if self.use_hv:
                    d['peds'] = 0
                if n:
                    d['nruns'] = int(n.group(1))
            elif low.startswith('first pedestal stalled'):
                self.set_slot(s, 'failed', 'first pedestal stalled')
            elif low.startswith('bias scan done'):
                n = re.search(r'(\d+) of (\d+) points', low)
                d = self.set_slot(s, 'done' if (n and int(n.group(1))) else 'failed', rest)
                if n:
                    d['points'] = int(n.group(1))
            elif low.startswith('done'):
                self.set_slot(s, 'done', 'done')
            elif low.startswith('exit'):
                code = re.search(r'exit (\d+)', low)
                code = code.group(1) if code else '?'
                if self.use_hv:
                    why = EXIT_REASON_HV.get(code, f'run_slot.sh exited {code}')
                    d = self.set_slot(s, 'gated' if code == '0' else 'failed', why)
                else:
                    why = EXIT_REASON.get(code, f'run_slot.sh exited {code}')
                    d = self.set_slot(s, 'done' if code == '0' else 'failed', why)
                d['exit'] = code
            else:
                self.set_slot(s, self.slot(s)['state'], rest)
            return s

        if current is None:
            return current

        m = _HVLINE.match(line)
        if m:
            cmd, status = m.group(1), m.group(2)
            try:
                payload = json.loads(m.group(3) or '{}')
            except ValueError:
                payload = {}
            d = self.slot(current)
            if 'current_A' in payload:
                d['leak_uA'] = round(float(payload['current_A']) * 1e6, 4)
            if status == 'fail':
                self.set_slot(current, 'failed', f'HV {cmd} failed')
            return current

        m = _TRY.match(line)
        if m:
            self.set_slot(current, 'bringup', f'bring-up try {m.group(1)} of {m.group(2)}')
            return current
        if _READY.match(line):
            self.set_slot(current, 'up', 'slot verified')
            return current
        if line.startswith('GATE: PASS'):
            self.set_slot(current, 'gated', 'gate passed')
            return current
        if line.startswith('GATE FAILED') or 'GATE: FAIL' in line:
            self.set_slot(current, 'gate-failed', 'gate failed')
            return current
        if _PEDROW.match(line):
            d = self.slot(current)
            d['peds'] += 1
            if d['state'] == 'pedestal':
                bv = d['bv']
                d['stage'] = (f"pedestal {d['peds']}/{d['nruns'] or '?'} done"
                              + (f' at {bv} V' if bv is not None else ''))
            return current
        return current

    # --- running the makefile -------------------------------------------------
    def run_command(self, cmd, logger=None):
        """Run cmd in its own process group (so Stop kills only this lane), streaming into the log."""
        env = dict(os.environ, **self.env())
        shown = ' '.join(f'{k}={v}' for k, v in self.env().items()
                         if k in ('MMTS_KRIA_IP', 'MMTS_PULLER_PORT'))
        self.log.append(f'$ {shown} {cmd}')
        ### every line also goes to a file: the page pane only holds the tail
        os.makedirs(self.pause_dir, exist_ok=True)
        job = re.search(r'JobName=(\w+)', cmd)
        job = job.group(1) if job else 'cmd'
        kind = self.runtag if job == 'Run' and self.runtag else \
            f"{self.name}_{job}_{time.strftime('%Y%m%d_%H%M%S')}"
        self.logfile = os.path.join(self.pause_dir, kind + '.log')
        flog = open(self.logfile, 'a', buffering=1)
        flog.write(f'$ {shown} {cmd}\n')
        if logger:
            logger.info(f'[{self.name}] {shown} {cmd}')
        process = subprocess.Popen(cmd, shell=True, env=env, text=True, bufsize=1,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        self.proc = process
        current = None
        try:
            for line in process.stdout:
                if logger:
                    logger.info(f'[{self.name}]{line.rstrip()}')
                flog.write(line if line.endswith('\n') else line + '\n')
                current = self.parse_progress(line, current)
                if self.stop_flag.is_set():
                    break
        except Exception as e:  # noqa: BLE001  (a broken pipe must not kill the lane)
            self.log.append(f'*** run_command: {e}')
        finally:
            if self.stop_flag.is_set():
                self.kill_group()
            process.wait()
            flog.write(f'[exit {process.returncode}  {time.strftime("%H:%M:%S %Z")}]\n')
            flog.close()
            self.proc = None
        return process.returncode

    def end_client_session(self, timeout=30):
        """End this lane's client session (the scans), so a hung run can be joined."""
        root = os.path.dirname(os.path.dirname(os.path.dirname(self.pause_dir)))
        # no single quotes (on_client.sh), pkill by session id, not by pattern
        cmd = ('f="$MMTS_ROOT/gui_lanes/$MMTS_LANE.sid"; s=$(cat "$f" 2>/dev/null); '
               'case "$s" in ""|*[!0-9]*|0|1) ;; *) pkill -s "$s";; esac; true')
        env = dict(os.environ, **self.env(), MMTS_LANE_TRACK='0')
        try:
            subprocess.run(['bash', os.path.join(root, 'scripts/task4_mmts_pedestal/on_client.sh'), cmd],
                           env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            pass

    def kill_group(self):
        p = self.proc
        if p and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

    def start(self, kind, target):
        t = threading.Thread(target=target, daemon=True)
        self.threads[kind] = t
        t.start()
        return t

    def join(self, kind):
        t = self.threads.get(kind)
        if t and t.is_alive():
            t.join()

    # --- the HV cable pause ---------------------------------------------------
    @property
    def pause_file(self):
        return os.path.join(self.pause_dir, 'hv_pause.json')

    @property
    def continue_file(self):
        return os.path.join(self.pause_dir, 'hv_continue')

    def read_pause(self):
        try:
            with open(self.pause_file) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def clear_pause(self):
        for f in (self.pause_file, self.continue_file):
            try:
                os.remove(f)
            except OSError:
                pass

    # --- what the page sees -----------------------------------------------------
    def snapshot(self, nlog=300):
        return {'name': self.name, 'kria': self.kria, 'port': self.port, 'hv_row': self.hv_row,
                'status': self.status, 'use_hv': self.use_hv,
                'probe': self.conf.get('skipPROBE') == '0',
                'runtag': self.runtag, 'logfile': os.path.basename(self.logfile),
                'paused': self.read_pause(),
                'slots': {s: dict(d) for s, d in list(self.slots.items())},
                'log': list(self.log)[-nlog:]}


def parse_krias(bench):
    """MMTS_bench.krias as [(host, name)]; an entry is a host or {host:, name:}."""
    out = []
    for k in bench.get('krias') or []:
        if isinstance(k, dict):
            host, name = str(k.get('host') or '').strip(), str(k.get('name') or '').strip()
        else:
            host, name = str(k).strip(), ''
        if host:
            out.append((host, name or host.split('.')[0]))
    return out


def load_lanes(bench, root='.'):
    """Lanes from MMTS_bench.lanes, else 8 lanes seeded from MMTS_bench.krias."""
    cfg = bench.get('lanes') or []
    if not cfg:
        krias = [h for h, _n in parse_krias(bench)]
        cfg = [{'kria': krias[i] if i < len(krias) else ''} for i in range(MAX_LANES)]
    lanes = []
    for i, c in enumerate(cfg[:MAX_LANES]):
        c = c or {}
        lanes.append(Lane(f'S{i + 1}', str(c.get('kria') or '').strip(),
                          int(c.get('puller_port') or BASE_PORT + i + 1), root,
                          c.get('hv_row') or i + 1))
    return lanes
