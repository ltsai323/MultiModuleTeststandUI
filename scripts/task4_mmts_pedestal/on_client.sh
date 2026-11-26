#!/usr/bin/env bash
# on_client.sh 'command': run one command on the MMTS client host.
#
# The client host has daq-client, unpack, ROOT and the $MM scripts. It is remote
# when MMTS_bench.client_host is set, local when empty; this is the ONLY place in
# task4 that knows which. A login shell runs the command, so ~/.bashrc exports apply.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
CONF="${MMTS_CONF:-$ROOT/data/mmts_configurations.yaml}"

cfg() { python3 "$ROOT/scripts/access_yaml_var.py" "$CONF" "MMTS_bench.$1"; }

[ $# -ge 1 ] || { echo "usage: on_client.sh 'command'" >&2; exit 2; }
CMD="$1"

# A GUI lane (one of up to 8 Krias) gets its own puller port and registry file,
# so lanes never share a daq-client or a slot letter.
if [ -n "${MMTS_REGISTRY_NAME:-}" ]; then
    case "$MMTS_REGISTRY_NAME" in *[!A-Za-z0-9._-]*) echo "bad MMTS_REGISTRY_NAME" >&2; exit 2;; esac
    CMD='export MMTS_REGISTRY="${RESULTS_DIR:-$MMTS_ROOT/Results}/'"$MMTS_REGISTRY_NAME"'"; '"$CMD"
fi
if [ -n "${MMTS_PULLER_PORT:-}" ]; then
    case "$MMTS_PULLER_PORT" in *[!0-9]*) echo "bad MMTS_PULLER_PORT" >&2; exit 2;; esac
    CMD="export PULLER_PORT=$MMTS_PULLER_PORT; $CMD"
fi
if [ -n "${MMTS_LANE:-}" ]; then
    case "$MMTS_LANE" in *[!A-Za-z0-9_]*) echo "bad MMTS_LANE" >&2; exit 2;; esac
    CMD="export MMTS_LANE=$MMTS_LANE; $CMD"
fi

# Room conditions for the hexmap titles (hexmap_robust.py); numbers only.
for v in MMTS_TEMP MMTS_RH; do
    val="${!v:-}"
    case "$val" in "") ;; *[!0-9.-]*) echo "bad $v" >&2; exit 2;; *) CMD="export $v=$val; $CMD";; esac
done

# The Kria picked in the GUI overrides the client's ~/.bashrc KRIA_IP.
if [ -n "${MMTS_KRIA_IP:-}" ]; then
    CMD="export KRIA_IP=$(printf %q "$MMTS_KRIA_IP"); $CMD"
fi

# A lane's run commands record their session id, so the lane's Stop can end
# exactly its own processes (pkill -s) and leave the other Krias' runs alone.
TRACK=0
[ -n "${MMTS_LANE:-}" ] && [ "${MMTS_LANE_TRACK:-0}" = "1" ] && TRACK=1

# MMTS_DRYRUN=1 prints the command and runs nothing, so the whole job can be
# exercised on a laptop with no bench.
if [ "${MMTS_DRYRUN:-0}" = "1" ]; then
    if [ "$TRACK" = "1" ]; then
        printf '[dry-run] client (lane %s, tracked): %s\n' "$MMTS_LANE" "$CMD"
    else
        printf '[dry-run] client: %s\n' "$CMD"
    fi
    exit 0
fi

if [ "$TRACK" = "1" ]; then
    SID="\$MMTS_ROOT/gui_lanes/$MMTS_LANE.sid"
    CMD="mkdir -p \"\$MMTS_ROOT/gui_lanes\"; exec setsid -w bash -c 'echo \$\$ > \"$SID\"; eval \"\$1\"; rc=\$?; rm -f \"$SID\"; exit \$rc' lane $(printf %q "$CMD")"
fi

HOST="$(cfg client_host)"
CLIENT_SHELL="$(cfg client_shell)"
CLIENT_SHELL="${CLIENT_SHELL:-bash -lc}"

if [ -z "$HOST" ]; then
    exec $CLIENT_SHELL "$CMD"
fi

# printf %q quotes the whole command as one argument for the remote login shell.
# BatchMode keeps a missing key from hanging the GUI on a password prompt.
exec ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST" "$CLIENT_SHELL $(printf %q "$CMD")"
