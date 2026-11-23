#!/usr/bin/env python3
"""Get the HV onto one mux slot, by cable or by relay (MMTS_bench.hv.switch).

    none    one cable moved by hand: pause file for the GUI, wait for Continue
    vitrek  Vitrek 964i: open every relay, close the module's, read back

    hv_switch.py none   --to B --from A          wait for the cable to be moved
    hv_switch.py vitrek --to B --row 3           relay of tray position 3C
    hv_switch.py vitrek --to B                   relay of mux slot B (one Kria)
    hv_switch.py none   --clear                  drop a stale pause file
    hv_switch.py vitrek --clear                  open every relay
    hv_switch.py vitrek --idn                    the Vitrek answers
    hv_switch.py vitrek --relays 7,22            parallel bias: exactly these relays closed
    hv_switch.py vitrek --to B --print-relay     the relay number only, no switching

Relays come from MMTS_channel_config: row MMTS_HV_ROW, slots A/B/C = positions L/C/R.
SAFETY: the caller must ramp to 0 V and turn the output off first, in both modes.
Exit 0 ok, 2 bad arguments, 3 switch refused, 4 no Continue within --timeout.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ON_CLIENT = os.path.join(ROOT, "scripts", "task4_mmts_pedestal", "on_client.sh")
SLOT_POS = {"A": "L", "B": "C", "C": "R"}

PAUSE = "hv_pause.json"      # written while waiting; the GUI reads the prompt
CONTINUE = "hv_continue"     # touched by the GUI's Continue button


def pause_dir(a):
    d = a.pause_dir or os.environ.get("MMTS_PAUSE_DIR") or os.path.join(ROOT, "logs")
    os.makedirs(d, exist_ok=True)
    return d


def clear(d):
    for f in (PAUSE, CONTINUE):
        try:
            os.remove(os.path.join(d, f))
        except OSError:
            pass


def wait_for_continue(a):
    """Prompt, then block until the GUI (or a shell) touches the continue file."""
    d = pause_dir(a)
    clear(d)
    where = f" from slot {a.frm}" if a.frm else ""
    prompt = (f"MOVE THE HV CABLE{where} to slot {a.to}, then press Continue."
              " The Keithley is at 0 V with the output off.")
    with open(os.path.join(d, PAUSE), "w") as f:
        json.dump({"prompt": prompt, "from": a.frm, "to": a.to, "since": time.time()}, f)

    print()
    print("#" * 72)
    print("##  " + prompt)
    print("##  (or from a shell: touch %s)" % os.path.join(d, CONTINUE))
    print("#" * 72)
    sys.stdout.flush()

    end = time.time() + a.timeout
    while time.time() < end:
        if os.path.exists(os.path.join(d, CONTINUE)):
            clear(d)
            print(f"HV switch ok cable moved to slot {a.to}")
            return 0
        time.sleep(1)
    clear(d)
    print(f"HV switch fail nobody pressed Continue in {a.timeout:.0f} s")
    return 4


def load_conf():
    import yaml
    path = os.environ.get("MMTS_CONF", os.path.join(ROOT, "data", "mmts_configurations.yaml"))
    with open(path) as f:
        return yaml.safe_load(f) or {}


def position(slot, row):
    return f"{int(row)}{SLOT_POS[slot]}" if row else slot


def relay_of(conf, slot, row):
    pos = position(slot, row)
    try:
        return pos, int(conf["MMTS_channel_config"][pos]["HVchannel"])
    except (KeyError, TypeError, ValueError):
        raise SystemExit(f"HV switch fail no HVchannel for position {pos} in MMTS_channel_config")


def term(v, default):
    """A yaml "\\n" arrives as a real newline; pass it on as an escape."""
    v = default if v in (None, "") else str(v)
    return v.encode("unicode_escape").decode()


def vitrek_cmd(conf, args):
    hw = (conf.get("MMTS_hardwares") or {})
    vt = hw.get("vitrek") or hw.get("vitek") or {}
    res = vt.get("Resource")
    if not res:
        raise SystemExit("HV switch fail no MMTS_hardwares.vitrek.Resource in the config")
    py = ((conf.get("MMTS_bench") or {}).get("hv") or {}).get("python") or "python3"
    return (f'{py} "$MM/vitrek.py" {args} --resource {shlex.quote(str(res))}'
            f' --baud {int(vt.get("BaudRate") or 9600)}'
            f' --read-term {shlex.quote(term(vt.get("ReadTermination"), chr(10)))}'
            f' --write-term {shlex.quote(term(vt.get("WriteTermination"), chr(10)))}')


class PortLock:
    """One vitrek.py at a time: two processes on one serial port both fail."""
    def __init__(self):
        self.path = os.environ.get("MMTS_VITREK_LOCK",
                                   os.path.join(os.environ.get("TMPDIR", "/tmp"), "mmts_vitrek.lock"))

    def __enter__(self):
        for _ in range(120):
            try:
                os.mkdir(self.path)
                return self
            except FileExistsError:
                ### no single vitrek.py call takes a minute; older is a crash
                if time.time() - os.path.getmtime(self.path) > 60:
                    os.rmdir(self.path)
                    continue
                time.sleep(1)
        raise SystemExit("HV switch fail the Vitrek port stayed busy for 2 minutes")

    def __exit__(self, *exc):
        try:
            os.rmdir(self.path)
        except OSError:
            pass


def on_client(cmd):
    env = dict(os.environ, MMTS_LANE_TRACK="0")
    return subprocess.call([ON_CLIENT, cmd], env=env)


def vitrek(a):
    """Open every relay and close the module's, on the client host, read back."""
    conf = load_conf()
    if a.idn:
        args, what = "idn", "answered"
    elif a.relays:
        args, what = f"route-many {a.relays}", f"relays {a.relays} closed (parallel bias)"
    elif a.clear:
        args, what = "reset", "every relay open"
    else:
        pos, relay = relay_of(conf, a.to, a.row)
        args, what = f"route {relay}", f"relay {relay} closed for position {pos}"
    with PortLock():
        rc = on_client(vitrek_cmd(conf, args))
    if rc != 0:
        print(f"HV switch fail vitrek.py {args} exited {rc}")
        return 3
    print(f"HV switch ok vitrek {what}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["none", "vitrek"])
    ap.add_argument("--to", dest="to", default="", help="slot A|B|C the HV should reach next")
    ap.add_argument("--from", dest="frm", default="", help="slot it is on now, for the prompt")
    ap.add_argument("--clear", action="store_true", help="reset the relays / drop a stale pause file")
    ap.add_argument("--timeout", type=float, default=3600.0, help="s to wait for Continue")
    ap.add_argument("--row", default=os.environ.get("MMTS_HV_ROW", ""),
                    help="vitrek: tray row 1..8 of this lane (default $MMTS_HV_ROW)")
    ap.add_argument("--idn", action="store_true", help="vitrek: check the instrument answers")
    ap.add_argument("--pause-dir", default="", help="where the pause and continue files live")
    ap.add_argument("--relays", default="", help="vitrek: comma list of relays to close together (parallel bias)")
    ap.add_argument("--print-relay", action="store_true", help="vitrek: print the relay of --to/--row and exit")
    a = ap.parse_args()

    if a.relays:
        if a.mode != "vitrek":
            print("HV switch fail --relays needs the Vitrek")
            return 2
        try:
            nums = [int(x) for x in a.relays.split(",") if x.strip()]
        except ValueError:
            nums = []
        if not nums:
            print(f"HV switch fail bad relay list {a.relays!r}")
            return 2
        a.relays = ",".join(str(n) for n in nums)
        return vitrek(a)

    if a.clear or a.idn:
        if a.mode == "vitrek":
            return vitrek(a)
        if a.idn:
            print("HV switch ok no switch to check (cable)")
            return 0
        clear(pause_dir(a))
        print("HV switch ok pause files cleared")
        return 0

    if a.to not in ("A", "B", "C"):
        print("HV switch fail --to must be A, B or C")
        return 2

    if a.print_relay:
        print(relay_of(load_conf(), a.to, a.row)[1])
        return 0

    # Dry run: skip the cable wait (the vitrek path is dry-run by on_client.sh).
    if a.mode == "none" and os.environ.get("MMTS_DRYRUN", "0") == "1":
        print(f"[dry-run] hv_switch none: HV to slot {a.to} (would wait for Continue)")
        return 0

    return vitrek(a) if a.mode == "vitrek" else wait_for_continue(a)


if __name__ == "__main__":
    sys.exit(main())
