# hv_lock.sh (sourced): the one Keithley belongs to ONE lane and slot at a time.
# Needs ROOT; lane name from MMTS_LANE ("solo" without one).
#
# Each slot's HV phase (route, on, leak check, bias points, off) holds the lock;
# bring-ups, gates and 0 V pedestals run in parallel without it.
# mkdir lock on the GUI host (atomic; macOS has no flock). The owner file holds
# "LANE SLOT PID"; a lock whose PID is gone is stale and may be taken over.

HV_LOCK="${MMTS_HV_SESSION_LOCK:-$ROOT/logs/hv_session.lock}"
HV_ME="${MMTS_LANE:-solo}"

hv_lock_owner() { cat "$HV_LOCK/owner" 2>/dev/null; }

hv_lock_stale() {
    [ -d "$HV_LOCK" ] || return 0
    local o pid
    o="$(hv_lock_owner)"
    if [ -z "$o" ]; then
        # mkdir done, owner not written yet: give the taker a moment
        sleep 1
        o="$(hv_lock_owner)"
        [ -z "$o" ] && return 0
    fi
    pid="${o##* }"
    ! kill -0 "$pid" 2>/dev/null
}

# hv_lock_try WHAT [PID]: take it now or fail. PID defaults to this shell.
hv_lock_try() {
    mkdir -p "$(dirname "$HV_LOCK")"
    if mkdir "$HV_LOCK" 2>/dev/null; then
        echo "$HV_ME $1 ${2:-$$}" > "$HV_LOCK/owner"
        return 0
    fi
    if hv_lock_stale; then
        echo "  hv lock: clearing a stale lock ($(hv_lock_owner))"
        rm -rf "$HV_LOCK"
        mkdir "$HV_LOCK" 2>/dev/null || return 1
        echo "$HV_ME $1 ${2:-$$}" > "$HV_LOCK/owner"
        return 0
    fi
    return 1
}

# hv_lock_acquire WHAT TIMEOUT_S SAYFN: wait for it, announcing the holder.
hv_lock_acquire() {
    local what="$1" timeout="${2:-14400}" say="${3:-echo}" t0 last=""
    t0=$(date +%s)
    while ! hv_lock_try "$what"; do
        local o; o="$(hv_lock_owner)"
        if [ "$o" != "$last" ]; then
            "$say" "${what}: waiting for the Keithley (held by ${o% *})"
            last="$o"
        fi
        [ $(( $(date +%s) - t0 )) -ge "$timeout" ] && return 1
        sleep 5
    done
    return 0
}

# Release only our own lock.
hv_lock_release() {
    local o; o="$(hv_lock_owner)"
    [ -n "$o" ] && [ "${o##* }" = "$$" ] && rm -rf "$HV_LOCK"
    return 0
}

# True when another lane's live process holds the Keithley.
hv_lock_held_by_other() {
    local o; o="$(hv_lock_owner)"
    [ -n "$o" ] && [ "${o%% *}" != "$HV_ME" ] && ! hv_lock_stale
}
