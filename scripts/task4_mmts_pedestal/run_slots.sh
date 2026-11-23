#!/usr/bin/env bash
# run_slots.sh: the Multi Pedestal Run, every filled slot one at a time.
#
# Reads its inputs from the environment (the makefile passes them):
#   moduleIDA moduleIDB moduleIDC   serials; an empty one skips that slot
#   powerBoardA/B/C                 auto (default) | fitted | none
#   nRUNS  label  skipPROBE  runTAG
#
# SEQUENTIAL: one Kria, one i2c-server, one daq-server, one trigger claim. Never -j.
# One slot failing does not stop the others.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ON_CLIENT="$HERE/on_client.sh"
PARAMS="$HERE/board_params.py"
COLLECT="$HERE/collect_plots.sh"

SLOTS="${slots:-A B C}"
NRUNS="${nRUNS:-5}"
LABEL="${label:-ped}"
SKIP_PROBE="${skipPROBE:-1}"
# Bring-up is a lottery; raise this when a slot keeps losing it.
TRIES="${bringupTRIES:-4}"
RUNTAG="${runTAG:-run1}"

case "$NRUNS"      in *[!0-9]*|'') echo "nRUNS must be a number, got '$NRUNS'";  exit 2;; esac
case "$LABEL"      in *[!A-Za-z0-9_-]*|'') echo "bad label '$LABEL'";            exit 2;; esac
case "$SKIP_PROBE" in 0|1) ;; *) echo "skipPROBE must be 0 or 1";                exit 2;; esac
case "$TRIES" in ""|*[!0-9]*) echo "bringupTRIES must be a number";           exit 2;; esac
[ "$TRIES" -ge 1 ] && [ "$TRIES" -le 40 ] || { echo "bringupTRIES must be 1..40"; exit 2; }

say() { printf '\n########## %s   [%s]\n' "$*" "$(date '+%H:%M:%S %Z')"; }

# MMTS_DRYRUN=1: on_client.sh prints each bench command instead of running it.
DRY="${MMTS_DRYRUN:-0}"
client() { "$ON_CLIENT" "$1"; }

# A GUI lane's run commands record their client session, so its Stop ends only
# this lane's processes. A no-op without MMTS_LANE.
export MMTS_LANE_TRACK=1

# --- resolve every slot BEFORE touching hardware ----------------------------
# A bad serial or type code stops the job here, before any bring-up.
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
    FILLED="$FILLED $S"
done
[ -n "$FILLED" ] || { echo "no slot has a module serial -- nothing to run"; exit 2; }

# --- the registry, once, before any bring-up --------------------------------
# run_slot.sh needs a registry entry; a stale one files data under the old serial.
REG=""
for S in $FILLED; do
    eval "REG=\"\$REG $S=\${${S}_SERIAL}\""
done
say "registering boards:$REG"
client "\"\$MM/register_boards.py\"$REG" \
    || { echo "register_boards.py failed -- not starting any bring-up"; exit 3; }

# --- the slots, one at a time -----------------------------------------------
RAN=0
for S in $FILLED; do
    eval "FAMILY=\${${S}_FAMILY}; BOARD=\${${S}_BOARD}; NROCS=\${${S}_NROCS}"
    eval "POWERFLAG=\${${S}_POWERFLAG}; DESC=\${${S}_DESC}; SERIAL=\${${S}_SERIAL}"

    say "$S: params $FAMILY $BOARD $NROCS ${POWERFLAG:---external-power}  ($SERIAL: $DESC)"

    # $MM stays literal here: it is the client host's own export.
    cmd=$(printf '%s SKIP_PROBE=%s BRINGUP_TRIES=%s "$MM/run_slot.sh" %s %s %s %s %s %s' \
          "$POWERFLAG" "$SKIP_PROBE" "$TRIES" "$S" "$FAMILY" "$BOARD" "$NROCS" "$LABEL" "$NRUNS")
    client "$cmd"
    rc=$?

    case $rc in
        0) why="pedestals ran" ;;
        1) why="bring-up failed" ;;
        2) why="probe gave no summary" ;;
        3) why="registry or link map refused" ;;
        4) why="delay scan gate failed -- pedestals not spent" ;;
        5) why="first pedestal stalled" ;;
        *) why="run_slot.sh exited $rc" ;;
    esac
    say "$S: EXIT $rc ($why)"
    [ $rc -eq 0 ] && RAN=$((RAN + 1))

    if [ "$DRY" = "1" ]; then
        echo "[dry-run] collect: $COLLECT $S $RUNTAG $LABEL"
    else
        "$COLLECT" "$S" "$RUNTAG" "$LABEL"
    fi
done

say "ALL SLOTS DONE -- $RAN of $(echo $FILLED | wc -w | tr -d ' ') slots produced pedestals"
[ "$RAN" -gt 0 ]
