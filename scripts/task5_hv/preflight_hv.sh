#!/usr/bin/env bash
# preflight_hv.sh: task4's read-only bench checks, plus the Keithley.
# Exit 0 = safe to run; any other exit = do not press Run.
#
# No power, no bring-up, no bias. `hv.py idn` resets the instrument (output OFF
# at 0 V), so it is safe and proves the cable, adapter and instrument answer.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"

bash "$ROOT/scripts/task4_mmts_pedestal/preflight.sh" || exit $?

printf '\n---------- preflight HV: the Keithley answers, and its polarity\n'
# Shared with the single-module stand (one stand holds HV at a time); idn proves
# the instrument, not that the cable is on THIS bench. Configured compliance used.
LIMIT_A="$(python3 "$ROOT/scripts/access_yaml_var.py" \
            "${MMTS_CONF:-$ROOT/data/mmts_configurations.yaml}" \
            MMTS_hardwares.keithley.CurrentLimit)"
LIMIT_UA="$(python3 -c "print(float('${LIMIT_A:-1.05e-3}') * 1e6)")"
"$HERE/hv.sh" idn --limit-ua "$LIMIT_UA" || {
    printf '\nPREFLIGHT FAILED: the Keithley did not answer.\n'
    printf '  - is the single-module stand holding it (its GUI open)?\n'
    printf '  - is the serial adapter still /dev/ttyUSB0 (check /dev/serial/by-id)?\n'
    exit 1; }

# Clear a stale pause file, or it would release the next run immediately.
python3 "$HERE/hv_switch.py" none --clear >/dev/null

printf '\nPREFLIGHT OK -- the bench and the Keithley are ready for Run\n'
printf 'Check which bench the HV cable is on before pressing Run.\n'
