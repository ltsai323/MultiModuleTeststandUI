#!/usr/bin/env python3
"""Parallel bias: keep the modules whose summed leakage fits the budget.

    hv_parallel_sum.py --budget-ua B --dir D LANE:RELAY ...

D/<LANE>.json holds that module's `HV leakcheck ok {...readings...}` line; a
module's leakage is its largest |reading|. The leakiest are left out until the
sum fits. Prints `sum ...` (one line for the log) and `keep LANE:RELAY ...`.
"""
import argparse
import json
import os


def leak_ua(path):
    try:
        line = open(path).read().strip()
        r = json.loads(line[line.index("{"):]).get("readings") or {}
        return max(abs(float(v)) for v in r.values()) * 1e6
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-ua", type=float, required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--unknown-ua", type=float, default=float("inf"),
                    help="leakage assumed without a reading (dry run: 0)")
    ap.add_argument("members", nargs="*")
    a = ap.parse_args()
    # no reading = unknown leakage = treated as the leakiest (by default)
    mods = [(m, leak_ua(os.path.join(a.dir, m.split(":")[0] + ".json"))) for m in a.members]
    mods = [(m, a.unknown_ua if u is None else u) for m, u in mods]
    keep = sorted(mods, key=lambda x: x[1])
    out = []
    while keep and sum(u for _, u in keep) > a.budget_ua:
        out.append(keep.pop())
    total = sum(u for _, u in keep)
    order = {m: i for i, m in enumerate(a.members)}
    keep.sort(key=lambda x: order[x[0]])
    fmt = lambda u: "?" if u == float("inf") else "%.3g" % u
    msg = "summed leakage %.3g uA of %s modules, budget %.4g uA" % (total, len(keep), a.budget_ua)
    if out:
        msg += "; left out (leakiest first): " + ", ".join(
            "%s %s uA" % (m.split(":")[0], fmt(u)) for m, u in out)
    print("sum " + msg)
    print("keep " + " ".join(m for m, _ in keep))


if __name__ == "__main__":
    main()
