#!/usr/bin/env bash
# collect_plots.sh SLOT RUNTAG [LABEL]: copy a slot's newest hexmaps into the gallery.
#
# From (client): $RESULTS_DIR/<serial>/Mux<S>_<label>/pedestal_run/run_<UTC>/
# To (GUI host): DataLoc/daqplots/<runTAG>/<S>-adc_mean.png and friends.
# Missing plots are not an error: a slot whose bring-up failed has none.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
ON_CLIENT="$HERE/on_client.sh"
CONF="${MMTS_CONF:-$ROOT/data/mmts_configurations.yaml}"

SLOT="${1:?slot A|B|C}"
RUNTAG="${2:?run tag, e.g. run1}"
LABEL="${3:-ped}"

# These three are interpolated into a command that runs on the client host.
case "$SLOT"   in A|B|C) ;; *) echo "collect_plots: slot must be A, B or C"; exit 2;; esac
case "$RUNTAG" in *[!A-Za-z0-9_-]*|'') echo "collect_plots: bad run tag"; exit 2;; esac
case "$LABEL"  in *[!A-Za-z0-9_-]*|'') echo "collect_plots: bad label";   exit 2;; esac

CLIENT="$(python3 "$ROOT/scripts/access_yaml_var.py" "$CONF" MMTS_bench.client_host)"
DATALOC="$(python3 "$ROOT/scripts/access_yaml_var.py" \
            "${AndrewModuleTestingGUI_BASE:-$ROOT/external_packages/hgcal-module-testing-gui}/configuration.yaml" DataLoc)"
[ -n "$DATALOC" ] || { echo "collect_plots: DataLoc is not set"; exit 1; }
DEST="$DATALOC/daqplots/$RUNTAG"

# Stage on the client under $MMTS_ROOT/daqplots/<runTAG>/ with gallery names.
# The robust width is the one to compare boards on (adc_stdd is quantized).
staged=$("$ON_CLIENT" "
    set -u
    slot=$SLOT; label=$LABEL; runtag=$RUNTAG
"'
    serial=$("$MM/module_of.py" "$slot" 2>/dev/null)
    [ -n "$serial" ] || { echo "collect_plots: slot $slot is not in the registry, no plots"; exit 0; }
    runs="$RESULTS_DIR/$serial/Mux${slot}_${label}/pedestal_run"
    # newest run directory that actually holds maps
    src=""
    for d in $(ls -1d "$runs"/run_* 2>/dev/null | sort -r); do
        [ -f "$d/Mux${slot}_adc_mean.png" ] && { src="$d"; break; }
    done
    [ -n "$src" ] || { echo "collect_plots: no hexmaps under $runs"; exit 0; }
    out="$MMTS_ROOT/daqplots/$runtag"
    mkdir -p "$out"
    # Clear this slot first: run tags restart at run1 with the GUI.
    # (No apostrophes in here: the whole block is one single-quoted string.)
    rm -f "$out/${slot}-"*.png "$out/${slot}.serial"
    cp -f "$src/Mux${slot}_adc_mean.png"         "$out/${slot}-adc_mean.png"
    cp -f "$src/Mux${slot}_adc_stdd.png"         "$out/${slot}-adc_stdd.png"
    cp -f "$src/Mux${slot}_robust_adc_stdd.png"  "$out/${slot}-robust.png" 2>/dev/null
    # The gallery keys on the slot letter, so the serial goes in a side file.
    printf %s "$serial" > "$out/${slot}.serial"
    echo "collect_plots: STAGED slot $slot <- $(basename "$src")  ($serial)"
' 2>&1) || true
echo "$staged"
### Nothing staged (failed bring-up) is normal: no rsync, no error.
case "$staged" in *"collect_plots: STAGED"*) ;; *) exit 0;; esac

mkdir -p "$DEST"
if [ -z "$CLIENT" ]; then
    CLIENT_ROOT="$("$ON_CLIENT" 'echo "$MMTS_ROOT"')"
    cp -f "$CLIENT_ROOT/daqplots/$RUNTAG"/"$SLOT"-*.png "$DEST/" 2>/dev/null
    cp -f "$CLIENT_ROOT/daqplots/$RUNTAG/$SLOT.serial"  "$DEST/" 2>/dev/null
else
    # A remote MMTS_ROOT has to be resolved on the far side before rsync sees it.
    CLIENT_ROOT="$("$ON_CLIENT" 'echo "$MMTS_ROOT"')"
    rsync -a --include="$SLOT-*.png" --include="$SLOT.serial" --exclude='*' \
        "$CLIENT:$CLIENT_ROOT/daqplots/$RUNTAG/" "$DEST/" 2>/dev/null \
        || echo "collect_plots: rsync of slot $SLOT plots failed (run kept on the client)"
fi
ls -1 "$DEST" 2>/dev/null | sed "s/^/collect_plots: gallery has /"
