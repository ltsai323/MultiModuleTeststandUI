#!/usr/bin/env python3
"""hv_parallel.py: one Keithley biasing every lane's module at once (parallel bias).

Lanes gate the same slot, meet here, and the leader drives the Keithley while each
lane takes its own pedestals. Lanes meet through files under <dir> (members/, rounds/<S>.<N>/;
mkdir and rename are atomic). A round closes when no live member is still coming or
parallel_wait_s has passed; a dead pid counts as gone.

Commands (all take --lane, --pid): join, leave, at, done, enter, leak, wait-leak,
point, wait-point, pdone, quit, wait-pdone, finish, status. Exit 4 = timed out or cut short.
"""
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
POLL = float(os.environ.get("MMTS_HV_PARALLEL_POLL", "2"))


def gdir():
    return os.environ.get("MMTS_HV_PARALLEL_DIR", os.path.join(ROOT, "logs", "hv_parallel"))


def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def lane_key(name):
    m = re.search(r"(\d+)$", name or "")
    return (int(m.group(1)) if m else 10 ** 6, name)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def say(msg):
    print(f"parallel bias: {msg}", file=sys.stderr)
    sys.stderr.flush()


# --- members -----------------------------------------------------------------
def member_path(lane):
    return os.path.join(gdir(), "members", f"{lane}.json")


def members():
    d = os.path.join(gdir(), "members")
    out = {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".json"):
            m = read_json(os.path.join(d, f))
            if m and alive(m.get("pid")):
                out[f[:-5]] = m
    return out


def mark_done(lane, slots):
    m = read_json(member_path(lane))
    if not m:
        return
    m["done"] = sorted(set(m.get("done", [])) | set(slots))
    write_json(member_path(lane), m)


# --- rounds ------------------------------------------------------------------
def rdir(rid):
    return os.path.join(gdir(), "rounds", rid)


def rounds_of(slot):
    d = os.path.join(gdir(), "rounds")
    out = []
    for f in os.listdir(d) if os.path.isdir(d) else []:
        m = re.fullmatch(rf"{slot}\.(\d+)", f)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def open_round(slot):
    """The open round for slot, or a new one. Race-safe: mkdir decides."""
    while True:
        ns = rounds_of(slot)
        for n in reversed(ns):
            if not os.path.isdir(os.path.join(rdir(f"{slot}.{n}"), "closed")):
                return f"{slot}.{n}"
        rid = f"{slot}.{(ns[-1] + 1) if ns else 1}"
        try:
            os.makedirs(os.path.join(gdir(), "rounds"), exist_ok=True)
            os.mkdir(rdir(rid))
            write_json(os.path.join(rdir(rid), "opened.json"), {"t": time.time()})
            return rid
        except FileExistsError:
            continue


def ready_of(rid):
    d = os.path.join(rdir(rid), "ready")
    out = {}
    for f in os.listdir(d) if os.path.isdir(d) else []:
        if f.endswith(".json"):
            r = read_json(os.path.join(d, f))
            if r and alive(r.get("pid")):
                out[f[:-5]] = r
    return out


def pending(rid, slot):
    """Live members still on their way to this slot."""
    rdy = ready_of(rid)
    return sorted((n for n, m in members().items()
                   if slot in m.get("slots", []) and slot not in m.get("done", []) and n not in rdy),
                  key=lane_key)


def try_close(rid, slot, wait_s):
    """Close the round if nobody is on the way or the wait is over."""
    opened = (read_json(os.path.join(rdir(rid), "opened.json")) or {}).get("t", time.time())
    late = pending(rid, slot)
    if late and time.time() - opened < wait_s:
        return False, late
    try:
        os.mkdir(os.path.join(rdir(rid), "closed"))
    except FileExistsError:
        return True, late       # someone else closed it; their roster stands
    rdy = ready_of(rid)
    names = sorted(rdy, key=lane_key)
    roster = {"rid": rid, "slot": slot, "leader": names[0] if names else "",
              "members": [{"lane": n, "pid": rdy[n]["pid"], "relay": rdy[n]["relay"]} for n in names],
              "dropped": late, "closed_at": time.time()}
    write_json(os.path.join(rdir(rid), "roster.json"), roster)
    return True, late


def cmd_enter(a):
    mark_done_before(a.lane, a.slot)
    while True:
        rid = open_round(a.slot)
        write_json(os.path.join(rdir(rid), "ready", f"{a.lane}.json"),
                   {"pid": a.pid, "relay": a.relay, "t": time.time()})
        last = None
        while True:
            closed, late = try_close(rid, a.slot, a.wait)
            if closed:
                break
            if late != last:
                say(f"round {rid}: waiting for {' '.join(late)} (at most {a.wait:.0f} s from the first ready)")
                last = late
            time.sleep(POLL)
        roster = None
        for _ in range(60):
            roster = read_json(os.path.join(rdir(rid), "roster.json"))
            if roster:
                break
            time.sleep(0.5)
        if roster and any(m["lane"] == a.lane for m in roster["members"]):
            print(json.dumps(roster))
            return 0
        say(f"round {rid} closed without {a.lane}; joining the next round")


def mark_done_before(lane, slot):
    mark_done(lane, [s for s in "ABC" if s < slot])


# --- the leader and the members during a round -----------------------------
def roster_of(rid):
    return read_json(os.path.join(rdir(rid), "roster.json")) or {}


def leader_alive(rid):
    r = roster_of(rid)
    for m in r.get("members", []):
        if m["lane"] == r.get("leader"):
            return alive(m["pid"])
    return False


def finished(rid):
    return read_json(os.path.join(rdir(rid), "finished.json"))


def wait_until(pred, rid, timeout, need_leader=True):
    """pred() -> value or None. Returns (value, why) where why is '' or the reason it gave up."""
    end = time.time() + timeout
    while True:
        v = pred()
        if v is not None:
            return v, ""
        f = finished(rid)
        if f:
            return None, f"the round is over ({f.get('reason', '?')})"
        if need_leader and not leader_alive(rid):
            return None, "the bias leader is gone"
        if time.time() >= end:
            return None, f"no answer in {timeout:.0f} s"
        time.sleep(POLL)


def cmd_leak(a):
    write_json(os.path.join(rdir(a.rid), "leak", f"{a.target}.json"),
               {"status": a.status, "line": a.json, "t": time.time()})
    return 0


def cmd_wait_leak(a):
    p = os.path.join(rdir(a.rid), "leak", f"{a.lane}.json")
    v, why = wait_until(lambda: read_json(p), a.rid, a.timeout)
    if v is None:
        say(f"no leakage verdict for {a.lane}: {why}")
        return 4
    if v.get("line"):
        print(v["line"])
    return {"pass": 0, "abort": 3}.get(v.get("status"), 1)


def step_name(v):
    """A bias step: BV300, BV300_2 (a repeated voltage); also a bare number."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", v):
        raise argparse.ArgumentTypeError(f"bad bias step {v!r}")
    return v


def cmd_point(a):
    write_json(os.path.join(rdir(a.rid), f"point_{a.bv}.json"),
               {"bv": a.bv, "current_A": a.current_a, "t": time.time()})
    return 0


def cmd_wait_point(a):
    p = os.path.join(rdir(a.rid), f"point_{a.bv}.json")
    v, why = wait_until(lambda: read_json(p), a.rid, a.timeout)
    if v is None:
        say(f"{a.bv}: {why}")
        return 4
    print(json.dumps(v))
    return 0


def cmd_pdone(a):
    d = os.path.join(rdir(a.rid), "pdone")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{a.bv}_{a.lane}"), "w") as f:
        f.write(a.status + "\n")
    return 0


def cmd_quit(a):
    d = os.path.join(rdir(a.rid), "quit")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, a.lane), "w").close()
    return 0


def cmd_wait_pdone(a):
    """Every member in LANES has reported BV, quit, or died."""
    pids = {m["lane"]: m["pid"] for m in roster_of(a.rid).get("members", [])}
    want = [x for x in a.lanes.split(",") if x]

    def missing():
        out = []
        for n in want:
            if os.path.exists(os.path.join(rdir(a.rid), "pdone", f"{a.bv}_{n}")):
                continue
            if os.path.exists(os.path.join(rdir(a.rid), "quit", n)) or not alive(pids.get(n)):
                continue
            out.append(n)
        return out

    end = time.time() + a.timeout
    last = None
    while True:
        m = missing()
        if not m:
            return 0
        if m != last:
            say(f"{a.bv}: waiting for the pedestals of {' '.join(m)}")
            last = m
        if time.time() >= end:
            say(f"{a.bv}: {' '.join(m)} did not finish in {a.timeout:.0f} s; moving on")
            return 4
        time.sleep(POLL)


def cmd_finish(a):
    p = os.path.join(rdir(a.rid), "finished.json")
    if not os.path.exists(p):
        write_json(p, {"reason": a.reason, "t": time.time()})
    return 0


def cmd_status(a):
    f = finished(a.rid)
    if f and f.get("reason") != "done":
        print(f.get("reason", "?"))
        return 4
    if not f and not leader_alive(a.rid):
        print("the bias leader is gone")
        return 4
    return 0


def cmd_join(a):
    write_json(member_path(a.lane), {"pid": a.pid, "slots": a.slots.split(), "done": [], "t": time.time()})
    return 0


def cmd_leave(a):
    m = read_json(member_path(a.lane))
    if m and int(m.get("pid", -1)) == a.pid:
        try:
            os.remove(member_path(a.lane))
        except OSError:
            pass
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lane", default=os.environ.get("MMTS_LANE", "solo"))
    ap.add_argument("--pid", type=int, default=os.getppid())
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("join"); p.add_argument("--slots", required=True)
    sub.add_parser("leave")
    p = sub.add_parser("at"); p.add_argument("slot", choices="ABC")
    p = sub.add_parser("done"); p.add_argument("slot", choices="ABC")
    p = sub.add_parser("enter"); p.add_argument("slot", choices="ABC")
    p.add_argument("--relay", type=int, required=True)
    p.add_argument("--wait", type=float, default=900.0)
    p = sub.add_parser("leak"); p.add_argument("rid"); p.add_argument("target")
    p.add_argument("status", choices=["pass", "abort", "fail"]); p.add_argument("--json", default="")
    p = sub.add_parser("wait-leak"); p.add_argument("rid"); p.add_argument("--timeout", type=float, default=18000)
    p = sub.add_parser("point"); p.add_argument("rid"); p.add_argument("bv", type=step_name)
    p.add_argument("--current-a", default="")
    p = sub.add_parser("wait-point"); p.add_argument("rid"); p.add_argument("bv", type=step_name)
    p.add_argument("--timeout", type=float, default=7200)
    p = sub.add_parser("pdone"); p.add_argument("rid"); p.add_argument("bv", type=step_name)
    p.add_argument("status", choices=["ok", "fail"])
    p = sub.add_parser("quit"); p.add_argument("rid")
    p = sub.add_parser("wait-pdone"); p.add_argument("rid"); p.add_argument("bv", type=step_name)
    p.add_argument("lanes"); p.add_argument("--timeout", type=float, default=7200)
    p = sub.add_parser("finish"); p.add_argument("rid"); p.add_argument("reason")
    p = sub.add_parser("status"); p.add_argument("rid")
    a = ap.parse_args()

    if a.cmd == "at":
        mark_done_before(a.lane, a.slot)
        return 0
    if a.cmd == "done":
        mark_done(a.lane, [a.slot])
        return 0
    return {"join": cmd_join, "leave": cmd_leave, "enter": cmd_enter, "leak": cmd_leak,
            "wait-leak": cmd_wait_leak, "point": cmd_point, "wait-point": cmd_wait_point,
            "pdone": cmd_pdone, "quit": cmd_quit, "wait-pdone": cmd_wait_pdone,
            "finish": cmd_finish, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
