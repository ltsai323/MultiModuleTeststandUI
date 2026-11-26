#!/usr/bin/env bash
# hv_guard.sh: Stop's and Clear's "HV off" for one lane among several.
#   MMTS_LANE=K2 hvSwitch=vitrek hv_guard.sh
#
# Ramps the Keithley to 0, output off, opens every Vitrek relay, ONLY when the
# Keithley is free, stale or this lane's. Another lane's live HV is left alone
# so one Stop cannot discharge a module another lane is measuring.
# Holds the lock throughout so no lane ramps up in between.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
CONF="${MMTS_CONF:-$ROOT/data/mmts_configurations.yaml}"
. "$HERE/hv_lock.sh"

LIMIT_A="$(python3 "$ROOT/scripts/access_yaml_var.py" "$CONF" MMTS_hardwares.keithley.CurrentLimit)"
LIMIT_UA="$(python3 -c "print(float('${LIMIT_A:-1.05e-3}') * 1e6)")"
SWITCH_MODE="${hvSwitch:-$(python3 "$ROOT/scripts/access_yaml_var.py" "$CONF" MMTS_bench.hv.switch)}"

if hv_lock_held_by_other; then
    echo "[HV] the Keithley is held by $(hv_lock_owner | cut -d' ' -f1,2); $HV_ME leaves it alone"
    exit 0
fi

# Ours, stale or free: take it (over from our own dead run if needed).
o="$(hv_lock_owner)"
if [ -n "$o" ] && [ "${o%% *}" = "$HV_ME" ]; then
    rm -rf "$HV_LOCK"
fi
if ! hv_lock_try stop; then
    echo "[HV] the Keithley was just taken by $(hv_lock_owner | cut -d' ' -f1,2); $HV_ME leaves it alone"
    exit 0
fi
trap 'hv_lock_release' EXIT

rc=0
bash "$HERE/hv.sh" off --limit-ua "$LIMIT_UA" || rc=1
if [ "$SWITCH_MODE" = "vitrek" ]; then
    python3 "$HERE/hv_switch.py" vitrek --clear || rc=1
else
    python3 "$HERE/hv_switch.py" none --clear >/dev/null || true
fi
exit $rc
