#!/usr/bin/env bash
# hv.sh <hv.py arguments>: run one hv.py command on the client host.
#   hv.sh idn | hv.sh off | hv.sh set 300 --limit-ua 10 --settle 5
#
# The single call site for hv.py (the only Keithley driver), so the runner,
# the makefile and Stop share one interpreter and GUI directory from the config.
# Exit code is hv.py's: 0 ok, 3 abort (leakcheck over the limit), 1 fail.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
CONF="${MMTS_CONF:-$ROOT/data/mmts_configurations.yaml}"

cfg() { python3 "$ROOT/scripts/access_yaml_var.py" "$CONF" "$1"; }

HV_PY="$(cfg MMTS_bench.hv.python)";   HV_PY="${HV_PY:-python3}"
HV_GUI_DIR="$(cfg MMTS_bench.hv.gui_dir)"

# One hv.py at a time: two processes on the serial port both fail.
# mkdir lock, not flock: macOS has no flock(1) and mkdir is atomic.
LOCK="${MMTS_HV_LOCK:-${TMPDIR:-/tmp}/mmts_hv.lock}"
for _try in $(seq 1 120); do
    if mkdir "$LOCK" 2>/dev/null; then
        trap 'rmdir "$LOCK" 2>/dev/null' EXIT INT TERM
        break
    fi
    # A lock older than 5 min is a crashed caller (no hv.py command takes 2).
    if [ -d "$LOCK" ] && [ -z "$(find "$LOCK" -maxdepth 0 -mmin -5 2>/dev/null)" ]; then
        echo "  hv.sh: clearing a stale lock at $LOCK" >&2
        rmdir "$LOCK" 2>/dev/null
    fi
    [ "$_try" = 1 ] && echo "  hv.sh: another HV command is running, waiting..." >&2
    sleep 1
done

# Untracked, so a lane Stop cannot cut a ramp short (Stop calls hv.sh off itself).
MMTS_LANE_TRACK=0 "$ROOT/scripts/task4_mmts_pedestal/on_client.sh" \
    "${HV_GUI_DIR:+HV_GUI_DIR=$HV_GUI_DIR }$HV_PY \"\$MM/hv.py\" $*"
