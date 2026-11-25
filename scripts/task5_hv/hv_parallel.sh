# hv_parallel.sh (sourced by run_slots_hv.sh): parallel bias, one Keithley for
# every lane's slot (MMTS_bench.hv.parallel_bias). The first lane on the roster
# leads: all modules together first (pass if the sum is within both limits), else
# per module alone, relay + HV on + leakage check + HV off; leakiest left
# out until the sum fits parallel_sum_uA; then all relays closed, HV on once, and
# per BV every lane takes pedestals. Followers never touch the Keithley or Vitrek;
# stopping the LEADER ramps the whole round down. Relays move only with output off.
# leakCHECK=0 skips the checks: only the compliance protects the modules.

PAR_RID=""          # the round this lane is LEADING; the exit trap finishes it

par() { python3 "$HERE/hv_parallel.py" --lane "$HV_ME" --pid $$ "$@"; }

parallel_on_exit() {
    [ "${PARALLEL:-0}" = 1 ] || return 0
    if [ -n "$PAR_RID" ]; then
        par finish "$PAR_RID" "the leader $HV_ME stopped" 2>/dev/null
        PAR_RID=""
    fi
    par leave 2>/dev/null
    return 0
}

# parallel_slot S: this lane's slot S, from the gate to the end of its bias scan.
parallel_slot() {
    local S="$1" relay roster rid leader members
    relay=$(python3 "$SWITCH" vitrek --to "$S" --print-relay 2>&1) || {
        say "$S: $relay -- no HV for this slot"; return 1; }
    say "$S: waiting for the other shelves (parallel bias, up to ${PAR_WAIT} s)"
    roster=$(par enter "$S" --relay "$relay" --wait "$PAR_WAIT") || {
        say "$S: could not join the parallel bias -- no HV for this slot"; return 1; }
    read -r rid leader members <<EOF
$(python3 -c 'import json, sys
r = json.loads(sys.argv[1])
print(r["rid"], r["leader"], " ".join("%s:%s" % (m["lane"], m["relay"]) for m in r["members"]))' "$roster")
EOF
    local dropped
    dropped=$(python3 -c 'import json, sys; print(" ".join(json.loads(sys.argv[1]).get("dropped", [])))' "$roster")
    echo "parallel bias round $rid: biased together:$(for m in $members; do printf ' %s (relay %s)' "${m%%:*}" "${m##*:}"; done); leader $leader${dropped:+; not waited for: $dropped}"
    if [ "$leader" = "$HV_ME" ]; then
        parallel_lead "$S" "$rid" "$members"
    else
        parallel_follow "$S" "$rid" "$leader"
    fi
}

parallel_lead() {
    local S="$1" rid="$2" members="$3" m lane r out lrc verdict line passed="" mine=0 followers=""
    PAR_RID="$rid"
    hv_take "$S" || {
        say "$S: the Keithley never came free -- no HV for this round"
        par finish "$rid" "the Keithley never came free"; PAR_RID=""; return 1; }
    local ptmp; ptmp=$(mktemp -d "${TMPDIR:-/tmp}/hvpar.XXXXXX")

    if [ "$LEAKCHK" = 0 ]; then
        # no checks: every module passes, nothing to sum
        echo "---- parallel bias: leakage check SKIPPED (leakCHECK=0): every module joins; only the ${LIMIT_UA} uA compliance protects them"
        for m in $members; do
            lane="${m%%:*}"
            par leak "$rid" "$lane" pass --json 'HV leakcheck skipped {"leakCHECK": 0}'
            [ "$lane" = "$HV_ME" ] && mine=1 || followers="$followers,$lane"
        done
        passed="$members"
    else
    # All together first: a module's current is at most the sum, so a passing sum passes everyone.
    local together=0 nall rlall cap
    nall=$(echo $members | wc -w | tr -d ' ')
    cap=$(python3 -c "print('%g' % min(float('$MAXLEAK'), float('$PAR_SUM_UA')))")
    if [ "$nall" -gt 1 ]; then
        rlall=$(for m in $members; do printf '%s,' "${m##*:}"; done); rlall="${rlall%,}"
        say "$S: leakage check of all $nall modules together at ${LEAKV} V (relays $rlall), passes at ${cap} uA or less"
        if python3 "$SWITCH" vitrek --relays "$rlall" && hv on --limit-ua "$LIMIT_UA"; then
            out=$(hv leakcheck $LEAKV --limit-ua "$LIMIT_UA" --abort-ua "$cap" --settle "$SETTLE" 2>&1); lrc=$?
            printf '%s\n' "$out"
            line=$(printf '%s\n' "$out" | grep -E '^HV leakcheck ok ' | tail -1)
            # every reading, 500 V included, within the cap
            [ $lrc -eq 0 ] && [ -n "$line" ] && python3 -c 'import json, sys
r = json.loads(sys.argv[1][sys.argv[1].index("{"):]).get("readings") or {}
sys.exit(0 if r and max(abs(float(v)) for v in r.values()) * 1e6 <= float(sys.argv[2]) else 1)' "$line" "$cap" \
                && together=1
        fi
        hv off --limit-ua "$LIMIT_UA" || echo "WARNING: hv.py off failed after the joint leakage check"
        if [ "$together" = 1 ]; then
            echo "---- parallel bias: all $nall modules pass together, no per-module checks needed"
            for m in $members; do
                lane="${m%%:*}"
                par leak "$rid" "$lane" pass --json "$line"
                [ "$lane" = "$HV_ME" ] && mine=1 || followers="$followers,$lane"
            done
            passed="$members"
        else
            echo "---- parallel bias: together over ${cap} uA or the check failed: one module at a time"
        fi
    fi
    if [ "$together" = 0 ]; then
    # One module at a time: the per-module leakage the shared bias cannot give.
    for m in $members; do
        lane="${m%%:*}"; r="${m##*:}"
        if [ "$lane" = "$HV_ME" ]; then
            say "$S: leakage check at ${LEAKV} V (relay $r alone)"
        else
            echo "---- parallel bias: leakage check of $lane at ${LEAKV} V (relay $r alone)"
        fi
        if ! python3 "$SWITCH" vitrek --relays "$r"; then
            par leak "$rid" "$lane" fail --json "HV leakcheck fail {\"error\": \"relay $r would not close\"}"
            continue
        fi
        if ! hv on --limit-ua "$LIMIT_UA"; then
            par leak "$rid" "$lane" fail --json 'HV leakcheck fail {"error": "HV would not turn on"}'
            hv off --limit-ua "$LIMIT_UA"
            continue
        fi
        out=$(hv leakcheck $LEAKV --limit-ua "$LIMIT_UA" --abort-ua "$MAXLEAK" --settle "$SETTLE" 2>&1); lrc=$?
        printf '%s\n' "$out" | sed "s/^/[$lane] /;s/^\[$HV_ME\] //"
        # output off before the next relay moves
        hv off --limit-ua "$LIMIT_UA" || echo "WARNING: hv.py off failed between leakage checks"
        case $lrc in 0) verdict=pass ;; 3) verdict=abort ;; *) verdict=fail ;; esac
        line=$(printf '%s\n' "$out" | grep -E '^HV leakcheck ' | tail -1)
        if [ "$verdict" = pass ]; then
            # published after the sum check below
            printf '%s\n' "$line" > "$ptmp/$lane.json"
            passed="$passed $m"
        else
            par leak "$rid" "$lane" "$verdict" --json "$line"
        fi
        if [ "$verdict" != pass ] && [ "$lane" = "$HV_ME" ]; then
            if [ "$verdict" = abort ]; then
                say "$S: LEAKAGE ABORT -- more than ${MAXLEAK} uA below 500 V, no pedestals (still leading the round)"
            else
                say "$S: leakage check failed (exit $lrc) -- no pedestals (still leading the round)"
            fi
        fi
    done

    # The SUM must fit: leave out the leakiest until it does.
    local keep="" sumline
    sumline=$(python3 "$HERE/hv_parallel_sum.py" --budget-ua "$PAR_SUM_UA" --dir "$ptmp" \
        $([ "$DRY" = 1 ] && echo --unknown-ua 0) $passed)
    keep=$(printf '%s\n' "$sumline" | sed -n 's/^keep *//p')
    echo "---- parallel bias: $(printf '%s\n' "$sumline" | sed -n 's/^sum //p')"
    for m in $passed; do
        lane="${m%%:*}"
        case " $keep " in
            *" $m "*)
                par leak "$rid" "$lane" pass --json "$(cat "$ptmp/$lane.json")"
                [ "$lane" = "$HV_ME" ] && mine=1 || followers="$followers,$lane" ;;
            *)
                par leak "$rid" "$lane" fail --json "HV leakcheck fail {\"error\": \"left out: the round's summed leakage is over the parallel budget of ${PAR_SUM_UA} uA\"}"
                [ "$lane" = "$HV_ME" ] && say "$S: LEFT OUT of the parallel bias: summed leakage over ${PAR_SUM_UA} uA, no pedestals; check this module by hand (still leading the round)" ;;
        esac
    done
    passed="$keep"
    fi
    fi
    rm -rf "$ptmp"
    followers="${followers#,}"

    if [ -z "$passed" ]; then
        echo "---- parallel bias: no module passed the leakage check, no bias scan"
        par finish "$rid" "no module passed the leakage check"; PAR_RID=""
        hv_give; return 0
    fi

    # Every module that passed, together.
    local relays="" n=0
    for m in $passed; do relays="$relays,${m##*:}"; n=$((n + 1)); done
    relays="${relays#,}"
    say "$S: HV routing to every module of the round (Vitrek relays $relays)"
    python3 "$SWITCH" vitrek --relays "$relays" || {
        say "$S: the round's relays would not close -- no bias scan"
        par finish "$rid" "the relays would not close"; PAR_RID=""; hv_give; return 1; }
    say "$S: HV on, compliance ${LIMIT_UA} uA (parallel bias: $n modules on one Keithley)"
    hv on --limit-ua "$LIMIT_UA" || {
        say "$S: HV would not turn on -- no bias scan"
        par finish "$rid" "HV would not turn on"; PAR_RID=""; hv_give; return 1; }

    local BV TAG STEP LEAK LEAK_UA prc SLOT_POINTS=0 START
    for STEP in $SCANSTEPS; do
        BV=${STEP%%:*}; TAG=${STEP##*:}
        say "$S: BV ${BV} V$(step_note "$BV" "$TAG") -- ramp and read leakage (total of $n modules in parallel)"
        out=$(hv set "$BV" --limit-ua "$LIMIT_UA" --settle "$SETTLE" 2>&1); lrc=$?
        printf '%s\n' "$out"
        [ $lrc -eq 0 ] || { say "$S: could not reach ${BV} V -- stopping the round's scan"
                            par finish "$rid" "could not reach ${BV} V"; break; }
        LEAK=$(printf '%s\n' "$out" | sed -n 's/^HV set ok .*"current_A": *\([-0-9.eE+]*\).*/\1/p' | tail -1)
        LEAK_UA=$([ -n "$LEAK" ] && python3 -c "print('%.6g' % (float('$LEAK') * 1e6))" 2>/dev/null)
        # "=": argparse takes -1.2e-08 for an option (Forward bias reads negative)
        par point "$rid" "$TAG" --current-a="$LEAK"
        # the trim step: every lane trims its own module at this voltage
        if [ "$TAG" = TRIM ]; then
            if [ "$mine" = 1 ]; then
                trim_point "$S" "$BV" "$LEAK_UA" || {
                    say "$S: reference pedestal failed -- this module leaves the scan, the others go on"; mine=2; }
            fi
            [ -n "$followers" ] && par wait-pdone "$rid" "$TAG" "$followers"
            continue
        fi

        if [ "$mine" = 1 ]; then
            say "$S: pedestals 1..$NRUNS at ${TAG}$SLOT_SFX"
            START=$(date +%s)
            pedestals_at "$S" "$TAG" "$FAMILY" "$BOARD" "$EXT"; prc=$?
            if [ $prc -ne 0 ]; then
                say "$S: pedestals at ${TAG} failed (exit $prc$(void_note $prc)) -- this module leaves the scan, the others go on"
                mine=2
            else
                SLOT_POINTS=$((SLOT_POINTS + 1)); POINTS=$((POINTS + 1))
                if [ "$DRY" = "1" ]; then
                    echo "[dry-run] collect: $COLLECT $S ${RUNTAG}${SLOT_SFX}_${TAG} ${SLOT_LBL}_${TAG}"
                else
                    "$COLLECT" "$S" "${RUNTAG}${SLOT_SFX}_${TAG}" "${SLOT_LBL}_${TAG}"
                fi
            fi
        fi
        [ -n "$followers" ] && par wait-pdone "$rid" "$TAG" "$followers"
    done
    par finish "$rid" "done"; PAR_RID=""

    [ "$mine" != 0 ] && say "$S: bias scan done, $SLOT_POINTS of $(echo $BVLIST | wc -w | tr -d ' ') points"
    hv_give
    [ $SLOT_POINTS -gt 0 ] && RAN=$((RAN + 1))
    return 0
}

parallel_follow() {
    local S="$1" rid="$2" leader="$3" line lrc pt BV TAG STEP LEAK LEAK_UA prc SLOT_POINTS=0 START
    if [ "$LEAKCHK" = 0 ]; then
        say "$S: leakage check SKIPPED (leakCHECK=0) -- only the ${LIMIT_UA} uA compliance protects this module"
    else
        say "$S: leakage check at ${LEAKV} V (measured by the bias leader $leader)"
    fi
    line=$(par wait-leak "$rid"); lrc=$?
    [ -n "$line" ] && printf '%s\n' "$line"
    case $lrc in
        0) ;;
        3) say "$S: LEAKAGE ABORT -- more than ${MAXLEAK} uA below 500 V, no pedestals"; return 0 ;;
        4) say "$S: the round ended before this module's leakage check -- no pedestals"; return 1 ;;
        *) case "$line" in
               *"left out:"*) say "$S: LEFT OUT of the parallel bias: summed leakage over ${PAR_SUM_UA} uA, no pedestals; check this module by hand" ;;
               *) say "$S: leakage check failed -- no pedestals" ;;
           esac
           return 1 ;;
    esac

    for STEP in $SCANSTEPS; do
        BV=${STEP%%:*}; TAG=${STEP##*:}
        echo "---- parallel bias: waiting for $leader to reach ${BV} V ($TAG)"
        pt=$(par wait-point "$rid" "$TAG") || {
            say "$S: the round stopped before ${BV} V -- ending this slot's scan"; break; }
        LEAK=$(python3 -c 'import json, sys; print(json.loads(sys.argv[1]).get("current_A") or "")' "$pt")
        LEAK_UA=$([ -n "$LEAK" ] && python3 -c "print('%.6g' % (float('$LEAK') * 1e6))" 2>/dev/null)
        say "$S: BV ${BV} V -- set by the bias leader $leader (current is the total of every in parallel module)"
        [ -n "$LEAK" ] && printf 'HV set ok {"current_A": %s, "volts": %s, "in parallel": true}\n' "$LEAK" "$BV"
        if [ "$TAG" = TRIM ]; then
            if ! trim_point "$S" "$BV" "$LEAK_UA"; then
                par pdone "$rid" "$TAG" fail; par quit "$rid"
                say "$S: reference pedestal failed -- stopping this slot's scan"; break
            fi
            local cut
            if ! cut=$(par status "$rid"); then
                say "$S: the round ended during the trim ($cut) -- the bias may have dropped, stopping this slot's scan"
                par quit "$rid"; break
            fi
            par pdone "$rid" "$TAG" ok
            continue
        fi

        say "$S: pedestals 1..$NRUNS at ${TAG}$SLOT_SFX"
        START=$(date +%s)
        pedestals_at "$S" "$TAG" "$FAMILY" "$BOARD" "$EXT"; prc=$?
        # If the leader stopped DURING these pedestals the bias dropped: do not count them.
        local cut
        if cut=$(par status "$rid"); then :; else
            say "$S: the round ended during the ${TAG} pedestals ($cut) -- the bias may have dropped, this point is NOT counted"
            par quit "$rid"
            break
        fi
        if [ $prc -ne 0 ]; then
            par pdone "$rid" "$TAG" fail; par quit "$rid"
            say "$S: pedestals at ${TAG} failed (exit $prc$(void_note $prc)) -- stopping this slot's scan"
            break
        fi
        par pdone "$rid" "$TAG" ok
        SLOT_POINTS=$((SLOT_POINTS + 1)); POINTS=$((POINTS + 1))
        if [ "$DRY" = "1" ]; then
            echo "[dry-run] collect: $COLLECT $S ${RUNTAG}${SLOT_SFX}_${TAG} ${SLOT_LBL}_${TAG}"
        else
            "$COLLECT" "$S" "${RUNTAG}${SLOT_SFX}_${TAG}" "${SLOT_LBL}_${TAG}"
        fi
    done
    par quit "$rid"
    say "$S: bias scan done, $SLOT_POINTS of $(echo $BVLIST | wc -w | tr -d ' ') points"
    [ $SLOT_POINTS -gt 0 ] && RAN=$((RAN + 1))
    return 0
}
