#!/usr/bin/env bash
# preflight.sh: the read-only checks behind task4's Initialize. Exit 0 = safe to Run.
#
# Checks the client bench stack, the Kria on port 22, the puller port (free or
# ours), no second puller on 8888, then clears the GUI daqplots (a lane: only its
# own runs). Nothing powered or written on the bench; stops at the first problem.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
ON_CLIENT="$HERE/on_client.sh"
CONF="${MMTS_CONF:-$ROOT/data/mmts_configurations.yaml}"

step() { printf '\n---------- preflight %s\n' "$*"; }
fail() { printf '\nPREFLIGHT FAILED: %s\n' "$*" >&2; exit 1; }

CLIENT="$(python3 "$ROOT/scripts/access_yaml_var.py" "$CONF" MMTS_bench.client_host)"
printf 'client host: %s\n' "${CLIENT:-<this machine>}"

# --- 1. the bench stack -----------------------------------------------------
step '1/5  client host: site exports, the bench scripts, daq-client and unpack'
"$ON_CLIENT" '
    set -u
    : "${MMTS_ROOT:?not exported on the client host -- see instructions 0.5}"
    : "${KRIA_IP:?not exported on the client host -- see instructions 0.5}"
    : "${MM:?not exported on the client host -- see instructions 0.5}"
    echo "MMTS_ROOT=$MMTS_ROOT  KRIA_IP=$KRIA_IP  KRIA_USER=${KRIA_USER:-daq}"
    ls "$MM/run_slot.sh" "$MM/register_boards.py" "$MM/lib.sh"
    command -v daq-client unpack
' || fail "the client host is missing part of the bench stack (step 1 above)"

# --- 2. the hexacontroller --------------------------------------------------
# exec 3<> returns once connected; `cat < /dev/tcp/...` would sit until timeout (124).
step "2/5  hexacontroller answers on port 22"
"$ON_CLIENT" '
    set -u
    timeout 5 bash -c "exec 3<>/dev/tcp/$KRIA_IP/22" \
        && echo "$KRIA_IP:22 open" \
        || { echo "no route to $KRIA_IP:22 -- is the hexacontroller powered and on the network?"; exit 1; }
' || fail "the hexacontroller is not reachable from the client host"

# --- 3. port 6001 -----------------------------------------------------------
# A 6001 holder we do not own makes every scan report "no summary.json". On pi0 it is
# the single-module stand's daq-client.service: report it; the fix is systemctl, never pkill.
PORT="${MMTS_PULLER_PORT:-6001}"
step "3/5  port $PORT on the client host is free or ours"
"$ON_CLIENT" '
    set -u
    port=${PULLER_PORT:-6001}
    line=$(ss -ltnp 2>/dev/null | grep ":$port ")
    if [ -z "$line" ]; then echo "$port free"; exit 0; fi
    echo "$line"

    # ss -p names the process only when this account owns it.
    case "$line" in *\"daq-client\"*)
        echo "held by our own daq-client -- puller_restart will replace it"; exit 0;; esac
    if [ "$port" != 6001 ]; then
        echo
        echo "port $port is held by a process this account does not own. Pick another"
        echo "puller_port for this lane in MMTS_bench.lanes, or find the holder."
        exit 1
    fi

    # Service check FIRST, whatever our uid: puller_restart pkills daq-client by name,
    # so a root GUI would kill the single-module stand. is-active, as kill -0 gets EPERM.
    if systemctl is-active --quiet daq-client.service 2>/dev/null; then
        svc=$(systemctl show -p MainPID --value daq-client.service 2>/dev/null)
        echo
        echo "6001 is held by daq-client.service (pid ${svc:-unknown}), the single-module stand."
        echo "For this session:"
        echo "    sudo systemctl stop daq-client.service"
        echo "and when you are done:"
        echo "    sudo systemctl start daq-client.service"
        echo "Never pkill it."
        exit 1
    fi

    # -x on the process NAME, not -f: this script mentions daq-client.service.
    if pgrep -u "$(id -u)" -x daq-client >/dev/null 2>&1; then
        echo "held by our own daq-client -- puller_restart will replace it"
        exit 0
    fi
    echo
    echo "6001 is held by a process this account does not own. Find it before"
    echo "starting: a puller that is not ours makes every scan report no data."
    exit 1
' || fail "port $PORT on the client host is taken (step 3 above)"

# --- 4. one puller per Kria -------------------------------------------------
# The Kria pushes round-robin over 8888: a second puller anywhere takes half of every run.
step "4/5  no other puller is attached to the hexacontroller (port 8888)"
"$ON_CLIENT" '
    set -u
    peers=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "${KRIA_USER:-daq}@$KRIA_IP" \
                "ss -tn 2>/dev/null | grep 8888" 2>/dev/null | grep ESTAB)
    if [ -z "$peers" ]; then echo "no established peer on 8888"; exit 0; fi
    echo "$peers"

    # Our own puller is fine (puller_restart replaces it); only a peer on
    # ANOTHER machine steals half the stream.
    foreign="$peers"
    for ip in $(hostname -I 2>/dev/null); do
        foreign=$(printf "%s\n" "$foreign" | grep -v " ${ip}:" || true)
    done
    if [ -z "$foreign" ]; then
        echo "the only peer is this client host -- ours, puller_restart replaces it"
        exit 0
    fi

    echo
    echo "Another puller already holds this Kria stream. It will steal half of"
    echo "every run. Find it (the peer address above) and stop it first."
    exit 1
' || fail "a second puller is attached to the hexacontroller (step 4 above)"

# --- 5. the GUI's own plot directory ----------------------------------------
step "5/5  clearing the GUI daqplots directory"
DATALOC="$(python3 "$ROOT/scripts/access_yaml_var.py" \
            "${AndrewModuleTestingGUI_BASE:-$ROOT/external_packages/hgcal-module-testing-gui}/configuration.yaml" DataLoc)"
[ -n "$DATALOC" ] || fail "DataLoc is not set in the module testing GUI configuration"
mkdir -p "$DATALOC/daqplots"
# The only destructive step runs locally, not via on_client.sh, so honor MMTS_DRYRUN here.
# A lane clears only the runs tagged with its name.
PICK="*"
[ -n "${MMTS_LANE:-}" ] && PICK="${MMTS_LANE}_*"
if [ "${MMTS_DRYRUN:-0}" = "1" ]; then
    echo "[dry-run] would clear $DATALOC/daqplots/$PICK"
else
    /bin/rm -rf "$DATALOC"/daqplots/$PICK
    echo "cleared $DATALOC/daqplots/$PICK"
fi

printf '\nPREFLIGHT OK -- the bench is ready for Run\n'
