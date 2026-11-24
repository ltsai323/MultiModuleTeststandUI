#!/usr/bin/env bash
# run_slots_hv.sh: pedestals versus bias voltage, every filled slot, one at a time.
# Env (from makefile_task5): moduleIDA/B/C (empty skips the slot) powerBoardA/B/C
#   nRUNS label skipPROBE runTAG bringupTRIES biasVOLTS hvSwitch trimPEDS
#   hvParallel maxLEAK leakCHECK useHV temperature humidity
#
# task4's run_slots.sh with a bias loop. Per slot: bring-up and gate (run_slot.sh,
# no pedestal), take the Keithley (hv_lock.sh), route the HV, HV on, leakage check,
# then per BV: set, settle, nRUNS pedestals (ped_run.sh, no new bring-up), hexmaps.
# HV to 0 and output off ALWAYS, including on Stop and on any failure.
# SEQUENTIAL: one Kria, one i2c-server, one daq-server, one HV cable. Never -j.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
T4="$ROOT/scripts/task4_mmts_pedestal"
ON_CLIENT="$T4/on_client.sh"
PARAMS="$T4/board_params.py"
COLLECT="$T4/collect_plots.sh"
SWITCH="$HERE/hv_switch.py"
CONF="${MMTS_CONF:-$ROOT/data/mmts_configurations.yaml}"
. "$HERE/hv_lock.sh"

cfg() { python3 "$ROOT/scripts/access_yaml_var.py" "$CONF" "$1"; }

# A GUI lane's run commands record their client session, so its Stop ends only
# this lane's processes. hv.sh turns this off for its own calls.
export MMTS_LANE_TRACK=1

# Room conditions: numbers or empty, since they reach a client command line.
TEMP="${temperature:-}"; RH="${humidity:-}"
case "$TEMP" in *[!0-9.-]*) echo "temperature must be a number, got '$TEMP'"; exit 2;; esac
case "$RH"   in *[!0-9.]*)  echo "humidity must be a number, got '$RH'";      exit 2;; esac
printf '\n########## conditions: %s C, %s %%RH   [%s]\n' "${TEMP:-?}" "${RH:-?}" "$(date '+%H:%M:%S %Z')"
# on_client.sh hands these to every bench command: hexmap_robust.py puts them in the map title
export MMTS_TEMP="$TEMP" MMTS_RH="$RH"

# archive_runs SLOT DUT SINCE: no-HV runs into <serial>/hexmaps/ (HV runs archive in pedestals_at)
archive_runs() {
    case "${MMTS_DRYRUN:-0}" in 1) echo "[dry-run] archive: slot $1 $2"; return 0;; esac
    "$T4/on_client.sh" "
    slot=$1; dut=$2; since=$3; rtag='${runTAG:-}'
"'
    serial=$("$MM/module_of.py" "$slot" 2>/dev/null) || exit 0
    [ -n "$serial" ] || exit 0
    for d in "$RESULTS_DIR/$serial/$dut/pedestal_run"/run_*; do
        [ -f "$d/pedestal_run0.root" ] || continue
        MMTS_ARCHIVE=1 MMTS_ARCHIVE_SINCE="$since" MMTS_RUNTAG="$rtag" \
            "${MMTS_VENV:-$MMTS_ROOT/venv}/bin/python3" "$MM/hexmap_robust.py" "$d" 2>&1 | grep "^hexmap_archive"
    done; true
' || echo "WARNING: hexmap archive failed for slot $1 (the run itself is fine)"
}

# HV off: exactly the Multi Pedestal Run, with N pedestals per slot under the
# plain label. Nothing below this case runs, so the Keithley is never opened.
case "${useHV:-1}" in
    0) START=$(date +%s)
       bash "$T4/run_slots.sh"; rc=$?
       for S in ${slots:-A B C}; do
           eval "raw=\${moduleID$S:-}"
           [ -n "$raw" ] && archive_runs "$S" "Mux${S}_${label:-ped}" "$START"
       done
       exit $rc ;;
    1) ;;
    *) echo "useHV must be 0 or 1, got '${useHV}'"; exit 2 ;;
esac

SLOTS="${slots:-A B C}"
NRUNS="${nRUNS:-5}"
LABEL="${label:-ped}"
SKIP_PROBE="${skipPROBE:-1}"
TRIES="${bringupTRIES:-4}"
RUNTAG="${runTAG:-run1}"
BIAS="${biasVOLTS:-1,10,50,100,300,300,500}"

# HV settings: the form wins, then the config, then a safe default.
HVSWITCH="${hvSwitch:-$(cfg MMTS_bench.hv.switch)}"; HVSWITCH="${HVSWITCH:-none}"
SETTLE="$(cfg MMTS_bench.hv.settle_s)";             SETTLE="${SETTLE:-5}"
LEAKV="$(cfg MMTS_bench.hv.leak_check_volts | tr -d '[],')"
LEAKV="${LEAKV:-0 1 10 100 300}"
MAXLEAK="${maxLEAK:-$(cfg MMTS_bench.hv.leak_abort_uA)}"; MAXLEAK="${MAXLEAK:-1}"
# 0 = no leakage check: the bias loop has no abort of its own, so only the
# compliance protects the module.
LEAKCHK="${leakCHECK:-$(cfg MMTS_bench.hv.leak_check)}"
case "$LEAKCHK" in 0|false|False|FALSE|no) LEAKCHK=0 ;; *) LEAKCHK=1 ;; esac
PAUSE_TIMEOUT="$(cfg MMTS_bench.hv.pause_timeout_s)";     PAUSE_TIMEOUT="${PAUSE_TIMEOUT:-3600}"
# how long a slot waits for another lane to give the Keithley back
LOCK_TIMEOUT="$(cfg MMTS_bench.hv.lock_timeout_s)";       LOCK_TIMEOUT="${LOCK_TIMEOUT:-14400}"
# Compliance and the instrument ceiling are the Keithley's own, not the bench's.
LIMIT_A="$(cfg MMTS_hardwares.keithley.CurrentLimit)";    LIMIT_A="${LIMIT_A:-10e-6}"
LIMIT_UA="$(python3 -c "print(float('$LIMIT_A') * 1e6)")"
HVMAX="$(cfg MMTS_hardwares.keithley.MaxVoltage)";        HVMAX="${HVMAX:-800}"
# Parallel bias: every lane's slot S biased together by one Keithley (hv_parallel.sh).
PARALLEL="${hvParallel:-$(cfg MMTS_bench.hv.parallel_bias)}"
case "$PARALLEL" in 1|true|True|TRUE|yes) PARALLEL=1 ;; *) PARALLEL=0 ;; esac
PAR_WAIT="$(cfg MMTS_bench.hv.parallel_wait_s)";             PAR_WAIT="${PAR_WAIT:-900}"
# Trimming: at TRIM_V one untrimmed reference pedestal, then trim_run.sh, then
# the whole bias list on the trimmed config (named <label>_trimmed).
TRIM="${trimPEDS:-$(cfg MMTS_bench.hv.trim_pedestals)}"
case "$TRIM" in 0|false|False|FALSE|no) TRIM=0 ;; *) TRIM=1 ;; esac
TRIM_V="$(cfg MMTS_bench.hv.trim_volts)"; TRIM_V="${TRIM_V:-300}"
# the SUM of the round's leak-check currents must fit this; default half the compliance
PAR_SUM_UA="$(cfg MMTS_bench.hv.parallel_sum_uA)"; PAR_SUM_UA="${PAR_SUM_UA:-$(python3 -c "print(float('$LIMIT_UA') / 2)")}"

case "$NRUNS"      in *[!0-9]*|'') echo "nRUNS must be a number, got '$NRUNS'";  exit 2;; esac
case "$LABEL"      in *[!A-Za-z0-9_-]*|'') echo "bad label '$LABEL'";            exit 2;; esac
case "$SKIP_PROBE" in 0|1) ;; *) echo "skipPROBE must be 0 or 1";                exit 2;; esac
case "$TRIES" in ""|*[!0-9]*) echo "bringupTRIES must be a number";              exit 2;; esac
[ "$TRIES" -ge 1 ] && [ "$TRIES" -le 40 ] || { echo "bringupTRIES must be 1..40"; exit 2; }
case "$HVSWITCH"   in none|vitrek) ;; *) echo "hvSwitch must be none or vitrek"; exit 2;; esac
case "$PAR_WAIT"  in ''|*[!0-9]*) echo "parallel_wait_s must be a whole number of seconds"; exit 2;; esac
case "$TRIM_V"    in ''|*[!0-9]*) echo "trim_volts must be a whole number of volts"; exit 2;; esac
python3 -c "import sys; v = float(sys.argv[1]); sys.exit(0 if 0 < v <= float(sys.argv[2]) else 1)" "$PAR_SUM_UA" "$LIMIT_UA" 2>/dev/null ||
    { echo "parallel_sum_uA must be a number above 0 and at most the compliance ($LIMIT_UA uA), got '$PAR_SUM_UA'"; exit 2; }
if [ "$PARALLEL" = 1 ] && [ "$HVSWITCH" != "vitrek" ]; then
    echo "parallel bias needs the Vitrek (hvSwitch=vitrek): with one cable only one module can be biased"
    exit 2
fi

# Validate the bias list before anything is powered.
BVLIST=""
for bv in ${BIAS//,/ }; do
    case "$bv" in ""|*[!0-9]*) echo "biasVOLTS holds '$bv'; every entry is a whole number of volts"; exit 2;; esac
    [ "$bv" -le "$HVMAX" ] || { echo "biasVOLTS holds ${bv} V, above the instrument limit ${HVMAX} V"; exit 2; }
    BVLIST="$BVLIST $bv"
done
[ -n "$BVLIST" ] || { echo "biasVOLTS is empty -- nothing to scan"; exit 2; }
# One VOLTS:NAME step per entry, so a voltage may repeat: BV300, then BV300_2.
BVSTEPS=""
for bv in $BVLIST; do
    n=$(printf '%s\n' $BVSTEPS | grep -c "^$bv:")
    if [ "$n" -eq 0 ]; then BVSTEPS="$BVSTEPS $bv:BV$bv"; else BVSTEPS="$BVSTEPS $bv:BV${bv}_$((n + 1))"; fi
done

# the trim step leads the scan; it never goes above the list's own top
BVTOP=0
for bv in $BVLIST; do [ "$bv" -gt "$BVTOP" ] && BVTOP="$bv"; done
[ "$TRIM_V" -le "$BVTOP" ] || TRIM_V="$BVTOP"
SCANSTEPS="$BVSTEPS"
[ "$TRIM" = 1 ] && SCANSTEPS="$TRIM_V:TRIM$BVSTEPS"

# The leakage check must never probe HIGHER than the scan itself will reach.
BVMAX=0
for bv in $BVLIST; do [ "$bv" -gt "$BVMAX" ] && BVMAX="$bv"; done
KEPT=""
for lv in $LEAKV; do
    case "$lv" in ''|*[!0-9]*) continue;; esac
    [ "$lv" -le "$BVMAX" ] && KEPT="$KEPT $lv"
done
# Always screen the HIGHEST bias point: the bias loop has no leakage abort of its own.
case " $KEPT " in
    *" $BVMAX "*) ;;
    *) KEPT="$KEPT $BVMAX" ;;
esac
# 0 V always survives: it is the baseline every other reading is judged against.
LEAKV="${KEPT# }"
[ -n "$LEAKV" ] || LEAKV="0"

say() { printf '\n########## %s   [%s]\n' "$*" "$(date '+%H:%M:%S %Z')"; }

DRY="${MMTS_DRYRUN:-0}"
client() { "$ON_CLIENT" "$1"; }

# hv.sh is the single call site for hv.py; Stop and Destroy use it too.
hv() { "$HERE/hv.sh" "$@"; }

# Never leave voltage on a cable: the trap ramps to 0 and turns output off (Stop pkills us).
# Only while HV_TOUCHED (this run holds the Keithley): another lane may be biasing.
HV_TOUCHED=0
hv_take() {    # hv_take WHAT: wait for the Keithley, announce who holds it
    hv_lock_acquire "$1" "$LOCK_TIMEOUT" say || return 1
    HV_TOUCHED=1
}
hv_give() {    # ramp down, open the relays, release the Keithley
    [ "$HV_TOUCHED" = "1" ] || return 0
    say "HV off (ramp to 0, output off)"
    hv off --limit-ua "$LIMIT_UA" || echo "WARNING: hv.py off failed -- check the Keithley by hand"
    if [ "$HVSWITCH" = "vitrek" ]; then
        python3 "$SWITCH" vitrek --clear || echo "WARNING: the Vitrek did not confirm all relays open"
    fi
    hv_lock_release
    # Once is enough: on a signal both the INT/TERM trap and the EXIT trap fire.
    HV_TOUCHED=0
}
. "$HERE/hv_parallel.sh"
hv_safe_off() { parallel_on_exit; hv_give; }
trap 'hv_safe_off; exit 130' INT TERM
trap 'hv_safe_off' EXIT

# Resolve every slot BEFORE touching hardware.
FILLED=""
for S in $SLOTS; do
    case "$S" in A|B|C) ;; *) echo "MMTS_bench.slots holds '$S'; the mux board has A, B and C"; exit 2;; esac
    eval "raw=\${moduleID$S:-}"
    [ -n "$raw" ] || continue
    eval "override=\${powerBoard$S:-auto}"
    if ! out=$(python3 "$PARAMS" "$raw" --power "$override" --shell 2>&1); then
        echo "slot $S: $out"
        exit 2
    fi
    eval "$(echo "$out" | sed "s/^/${S}_/")"
    # The geometry's own ceiling, and the instrument's, whichever is lower.
    eval "bmax=\${${S}_MAXV}"
    [ "$bmax" -le "$HVMAX" ] || bmax="$HVMAX"
    for bv in $BVLIST; do
        [ "$bv" -le "$bmax" ] || {
            eval "d=\${${S}_DESC}"
            echo "slot $S ($d) takes at most ${bmax} V, and biasVOLTS asks for ${bv} V"
            exit 2; }
    done
    FILLED="$FILLED $S"
done
[ -n "$FILLED" ] || { echo "no slot has a module serial -- nothing to run"; exit 2; }

say "bias points:$BVLIST V ($(echo $BVSTEPS | sed "s/[0-9]*://g"))   compliance ${LIMIT_UA} uA   $([ "$LEAKCHK" = 1 ] && echo "leak check ${LEAKV} V, abort above ${MAXLEAK} uA" || echo "NO LEAKAGE CHECK (only the compliance protects the modules)")$([ "$TRIM" = 1 ] && echo "   trimming at ${TRIM_V} V first" || echo "   no trimming")"
say "HV routing: $HVSWITCH$([ "$HVSWITCH" = none ] && echo ' (one cable, moved by hand between slots)')$([ "$PARALLEL" = 1 ] && echo ", PARALLEL BIAS: one Keithley biases every lane's slot together (wait up to ${PAR_WAIT} s for the other lanes; $([ "$LEAKCHK" = 1 ] && echo "summed leakage at most ${PAR_SUM_UA} uA" || echo "no leakage check, every module joins"))")"
[ "$PARALLEL" = 1 ] && par join --slots "$FILLED"

# The instruments, once, with the Keithley's polarity in the banner. hv.py idn
# resets the Keithley, so it runs only while nobody else holds it.
if hv_lock_held_by_other; then
    say "HV instrument: in use by $(hv_lock_owner | cut -d' ' -f1,2), skipping the check"
elif hv_lock_try idn; then
    say "HV instrument"
    hv idn --limit-ua "$LIMIT_UA"; irc=$?
    if [ $irc -eq 0 ] && [ "$HVSWITCH" = "vitrek" ]; then
        python3 "$SWITCH" vitrek --idn; irc=$?
    fi
    hv_lock_release
    [ $irc -eq 0 ] || { echo "an HV instrument did not answer -- not starting any bring-up"; exit 3; }
else
    say "HV instrument: just taken by $(hv_lock_owner | cut -d' ' -f1,2), skipping the check"
fi

# The registry, once, before any bring-up.
REG=""
for S in $FILLED; do
    eval "REG=\"\$REG $S=\${${S}_SERIAL}\""
done
say "registering boards:$REG"
client "\"\$MM/register_boards.py\"$REG" \
    || { echo "register_boards.py failed -- not starting any bring-up"; exit 3; }

# nRUNS pedestals at one bias point, then the hexmaps.
step_note() {    # step_note BV TAG: " (BV300_2)", " (trim)" or nothing
    case "$2" in TRIM) echo " (trim)";; "BV$1") ;; *) echo " ($2)";; esac
}
void_note() { case "$1" in 8) echo ", the trims did not reach the chips";; 9) echo ", chips out of time: check EdgeSel_T1";; 10) echo ", no data: the links lost alignment";; esac; }

# trim_point S BV LEAK_UA (HV already at BV): reference pedestal, trim_run.sh, SLOT_*
# to the trimmed config. A failed trim runs untrimmed; returns 1 only if the reference failed.
trim_point() {
    local S="$1" BV="$2" LEAK_UA="$3" START prc out cfgp exp
    say "$S: pedestals 1..1 at BV${BV}, untrimmed reference"
    START=$(date +%s)
    pedestals_at "$S" "BV$BV" "$FAMILY" "$BOARD" "$EXT" 1; prc=$?
    [ $prc -eq 0 ] || return 1
    if [ "$DRY" = "1" ]; then
        echo "[dry-run] collect: $COLLECT $S ${RUNTAG}_BV${BV} ${LABEL}_BV${BV}"
    else
        "$COLLECT" "$S" "${RUNTAG}_BV${BV}" "${LABEL}_BV${BV}"
    fi

    say "$S: trimming at ${BV} V (pedestal_scan, vrefnoinv_scan, vrefinv_scan)"
    out=$(client "$(printf 'PED_BASECFG="$SCRIPTS/configs/%s_mux%s_ped.yaml" "$MM/trim_run.sh" %s Mux%s_%s_trim' \
                   "$FAMILY" "$S" "$S" "$S" "$LABEL")" 2>&1)
    printf '%s\n' "$out"
    if [ "$DRY" = "1" ]; then
        out="TRIMMED /dry-run/Mux${S}_${LABEL}_trim/trimmed_config.yaml
EXPECT roc_s0.sc.ReferenceVoltage.0.Inv_vref=400"
    fi
    cfgp=$(printf '%s\n' "$out" | sed -n 's/^TRIMMED //p' | tail -1)
    exp=$(printf '%s\n' "$out" | sed -n 's/^EXPECT //p' | tail -1)
    case "$cfgp$exp" in *[!A-Za-z0-9_./=,-]*) cfgp="" ;; esac     # both reach a client command line
    if [ -n "$cfgp" ]; then
        SLOT_CFG="$cfgp"; SLOT_EXPECT="$exp"; SLOT_SFX="_trimmed"; SLOT_LBL="${LABEL}_trimmed"
        say "$S: trimmed -- the bias scan runs on $cfgp"
    else
        say "$S: TRIMMING FAILED ($(printf '%s\n' "$out" | sed -n 's/^TRIM-FAILED //p' | tail -1)) -- the bias scan runs untrimmed"
    fi
    # the trim's many starts can leave a link unaligned: bring up again
    SLOT_FRESH=1
    return 0
}

# ped_run.sh, not run_slot.sh: the slot is already up; a second bring-up re-rolls it.
# Trim state rides in SLOT_CFG (empty = slot file), SLOT_EXPECT and SLOT_LBL.
# A bring-up cycles the module LV, so only at a bias of LOWBIAS_V or less.
LOWBIAS_V=10
SLOT_CFG=""; SLOT_EXPECT=""; SLOT_SFX=""; SLOT_LBL="$LABEL"; SLOT_FRESH=0
pedestals_at() {
    local S="$1" TAG="$2" FAMILY="$3" BOARD="$4" EXT="$5" N="${6:-$NRUNS}"     # TAG: BV300, BV300_2
    local bv="${TAG#BV}" low=0 first=0
    bv="${bv%%_*}"
    case "$bv" in ''|*[!0-9]*) ;; *) [ "$bv" -le "$LOWBIAS_V" ] && low=1 ;; esac
    if [ "$SLOT_FRESH" = 1 ]; then
        if [ "$low" = 1 ]; then
            first=1; SLOT_FRESH=0
            echo "---- fresh bring-up before these pedestals (after the trim, bias ${bv} V)"
        else
            echo "---- no fresh bring-up at ${bv} V: it cycles the module LV under bias"
        fi
    fi
    client "
    set -u
    export PED_BRINGUP_FIRST=$first PED_RETRY_BRINGUP=$low
    slot=$S; fam=$FAMILY; board=$BOARD; ext='$EXT'; n=$N
    dut=Mux${S}_${SLOT_LBL}_${TAG}; lab=${SLOT_LBL}_${TAG}
    trimcfg='$SLOT_CFG'; expect='$SLOT_EXPECT'
    since='${START:-0}'; leak='${LEAK_UA:-}'; rtag='${runTAG:-}'
"'
    serial=$("$MM/module_of.py" "$slot" 2>/dev/null)
    [ -n "$serial" ] || { echo "slot $slot is not in the registry"; exit 3; }
    tmp=$(mktemp)
    PED_BASECFG="${trimcfg:-$SCRIPTS/configs/${fam}_mux${slot}_ped.yaml}" PED_DUT="$dut" \
    PED_BOARD="$board" PED_EXTPOWER="$ext" PED_EXPECT="$expect" \
        "$MM/ped_run.sh" "$slot" "$n" "$lab" 10000 | tee "$tmp"
    rc=${PIPESTATUS[0]}
    void=$(grep -c "VOID:" "$tmp"); rm -f "$tmp"
    # the readback disagrees with the trimmed config: the trims are not on the chips
    [ "$void" -eq 0 ] || { echo "TRIMS NOT ON THE CHIPS: the ROC readback disagrees with the trimmed config"; exit 8; }
    [ "$rc" -eq 0 ] || exit "$rc"
    runs="$RESULTS_DIR/$serial/$dut/pedestal_run"
    echo "--- finder header positions (23 everywhere = right edge)"
    "$MM/finder_positions.sh" "$runs"/run_* 2>/dev/null | tail -3
    for d in "$runs"/run_*; do
        [ -f "$d/pedestal_run0.root" ] || continue
        echo "=== $(basename "$d")"
        # The bench venv: a bare python3 here is the GUI .venv, without uproot3.
        # MMTS_ARCHIVE: also copy the maps to <serial>/hexmaps/ for the gallery
        MMTS_ARCHIVE=1 MMTS_ARCHIVE_SINCE="$since" MMTS_LEAK_UA="$leak" MMTS_RUNTAG="$rtag" \
        "${MMTS_VENV:-$MMTS_ROOT/venv}/bin/python3" "$MM/hexmap_robust.py" "$d" 2>&1 \
            | grep -E "adc_stdd|above|Error|hexmap_archive" || true
    done   # a grep with no match must not turn a good pedestal into "failed"
'
}

# The slots, one at a time.
RAN=0
POINTS=0
PREV=""
for S in $FILLED; do
    eval "FAMILY=\${${S}_FAMILY}; BOARD=\${${S}_BOARD}; NROCS=\${${S}_NROCS}"
    eval "POWERFLAG=\${${S}_POWERFLAG}; DESC=\${${S}_DESC}; SERIAL=\${${S}_SERIAL}"
    [ "$PARALLEL" = 1 ] && par at "$S"
    # run_slot.sh's POWER= (board fitted) is ped_run.sh's PED_EXTPOWER= (empty).
    EXT=1; [ -n "$POWERFLAG" ] && EXT=""

    # Cable: route before the bring-up so the operator moves it once (output off).
    if [ "$HVSWITCH" = "none" ]; then
        hv_take "$S" || { say "$S: the Keithley never came free -- skipping this slot"; continue; }
        say "$S: HV routing to slot $S"
        python3 "$SWITCH" none --to "$S" ${PREV:+--from "$PREV"} --timeout "$PAUSE_TIMEOUT"
        srcw=$?
        PREV="$S"
        if [ $srcw -ne 0 ]; then
            say "$S: HV could not be routed (hv_switch exited $srcw) -- skipping this slot"
            hv_give
            continue
        fi
    fi

    say "$S: params $FAMILY $BOARD $NROCS ${POWERFLAG:---external-power}  ($SERIAL: $DESC)"
    SLOT_CFG=""; SLOT_EXPECT=""; SLOT_SFX=""; SLOT_LBL="$LABEL"; SLOT_FRESH=0

    # bring-up + gate, no pedestal. $MM stays literal: the client exports it.
    say "$S: bring-up and gate"
    START=$(date +%s)
    cmd=$(printf '%s SKIP_PROBE=%s BRINGUP_TRIES=%s "$MM/run_slot.sh" %s %s %s %s %s 0' \
          "$POWERFLAG" "$SKIP_PROBE" "$TRIES" "$S" "$FAMILY" "$BOARD" "$NROCS" "${LABEL}_gate")
    client "$cmd"
    rc=$?
    case $rc in
        0) why="gate passed" ;;
        1) why="bring-up failed" ;;
        2) why="probe gave no summary" ;;
        3) why="registry or link map refused" ;;
        4) why="delay scan gate failed -- no HV applied" ;;
        5) why="first pedestal stalled -- no HV applied" ;;
        *) why="run_slot.sh exited $rc" ;;
    esac
    say "$S: EXIT $rc ($why)"
    [ $rc -eq 0 ] || { hv_give; [ "$PARALLEL" = 1 ] && par done "$S"; continue; }

    # Parallel bias: the lanes bias this slot together, one Keithley.
    if [ "$PARALLEL" = 1 ]; then
        parallel_slot "$S"
        par done "$S"
        continue
    fi

    # Vitrek: the relay, after the gate, with the Keithley held.
    if [ "$HVSWITCH" = "vitrek" ]; then
        hv_take "$S" || { say "$S: the Keithley never came free -- no HV for this slot"; continue; }
        say "$S: HV routing to slot $S (Vitrek)"
        python3 "$SWITCH" vitrek --to "$S"
        srcw=$?
        if [ $srcw -ne 0 ]; then
            say "$S: HV could not be routed (hv_switch exited $srcw) -- no HV for this slot"
            hv_give
            continue
        fi
    fi

    # HV, and only now.
    say "$S: HV on, compliance ${LIMIT_UA} uA"
    hv on --limit-ua "$LIMIT_UA" || { say "$S: HV would not turn on -- skipping this slot"; hv_give; continue; }

    if [ "$LEAKCHK" = 0 ]; then
        say "$S: leakage check SKIPPED (leakCHECK=0) -- only the ${LIMIT_UA} uA compliance protects this module"
        lrc=0
    else
        say "$S: leakage check at ${LEAKV} V"
        hv leakcheck $LEAKV --limit-ua "$LIMIT_UA" --abort-ua "$MAXLEAK" --settle "$SETTLE"
        lrc=$?
    fi
    if [ $lrc -eq 3 ]; then
        say "$S: LEAKAGE ABORT -- more than ${MAXLEAK} uA below 500 V, no pedestals"
        hv_give
        continue
    elif [ $lrc -ne 0 ]; then
        say "$S: leakage check failed (exit $lrc) -- no pedestals"
        hv_give
        continue
    fi

    SLOT_POINTS=0
    for STEP in $SCANSTEPS; do
        BV=${STEP%%:*}; TAG=${STEP##*:}
        say "$S: BV ${BV} V$(step_note "$BV" "$TAG") -- ramp and read leakage"
        # captured for the archive, then printed for the progress parser
        out=$(hv set "$BV" --limit-ua "$LIMIT_UA" --settle "$SETTLE" 2>&1); src=$?
        printf '%s\n' "$out"
        [ $src -eq 0 ] || { say "$S: could not reach ${BV} V -- stopping this slot's scan"; break; }
        LEAK=$(printf '%s\n' "$out" | sed -n 's/^HV set ok .*"current_A": *\([-0-9.eE+]*\).*/\1/p' | tail -1)
        LEAK_UA=$([ -n "$LEAK" ] && python3 -c "print('%.6g' % (float('$LEAK') * 1e6))" 2>/dev/null)
        if [ "$TAG" = TRIM ]; then
            trim_point "$S" "$BV" "$LEAK_UA" || { say "$S: reference pedestal failed -- stopping this slot's scan"; break; }
            continue
        fi

        say "$S: pedestals 1..$NRUNS at ${TAG}$SLOT_SFX"
        START=$(date +%s)
        pedestals_at "$S" "$TAG" "$FAMILY" "$BOARD" "$EXT"
        prc=$?
        if [ $prc -ne 0 ]; then
            say "$S: pedestals at ${TAG} failed (exit $prc$(void_note $prc)) -- stopping this slot's scan"
            break
        fi
        SLOT_POINTS=$((SLOT_POINTS + 1))
        POINTS=$((POINTS + 1))

        if [ "$DRY" = "1" ]; then
            echo "[dry-run] collect: $COLLECT $S ${RUNTAG}${SLOT_SFX}_${TAG} ${SLOT_LBL}_${TAG}"
        else
            "$COLLECT" "$S" "${RUNTAG}${SLOT_SFX}_${TAG}" "${SLOT_LBL}_${TAG}"
        fi
    done

    say "$S: bias scan done, $SLOT_POINTS of $(echo $BVLIST | wc -w | tr -d ' ') points"
    hv_give
    [ $SLOT_POINTS -gt 0 ] && RAN=$((RAN + 1))
done

say "ALL SLOTS DONE -- $RAN of $(echo $FILLED | wc -w | tr -d ' ') slots produced pedestals, $POINTS bias point(s) in total"
[ "$RAN" -gt 0 ]
