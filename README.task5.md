# Task5: the pedestal run, up to 8 Krias, HV optional

Since 2026-10-14 this page is the Multi Pedestal Run and the HV Pedestal Scan in
one, for up to **8 Krias in parallel**. Design and reasoning:
`docs/plan_multi_kria_lanes.md`.

## Lanes

Each Kria is a **lane** (S1 to S8, shown as "Shelf 1" to "Shelf 8"; K1 to K8 before 2026-11-23): its own card on the page with its own
address, slots A/B/C, Initialize, Configure, Run, Stop and **Clear**, LEDs and
log. Lanes run side by side; inside a lane the slots still run one at a time.
"Initialize all", "Configure all", "Run all", "Stop all" and "Clear all" act on
every lane that is ready for it.

```yaml
MMTS_bench:
  lanes:                       # optional; default = 8 lanes seeded from krias
    - {kria: kria6.physics.ucsb.edu, puller_port: 6101}
    - {kria: '',                     puller_port: 6102}
```

What keeps the lanes apart on the shared client host:

| | per lane | how |
|---|---|---|
| daq-client | port 6101..6108 | `PULLER_PORT` in `lib.sh`; restart and kill match only that port |
| module registry | `module_ids_<kria>.json` | `MMTS_REGISTRY` in `module_of.py` |
| Stop on the client | its own session | `on_client.sh` records it under `$MMTS_ROOT/gui_lanes/<lane>.sid`; Stop runs `pkill -s` |
| Stop on the GUI host | its own process group | `start_new_session` in `lanes.py` |
| gallery | runs tagged `K<n>_run<m>` | Initialize clears only its own lane's runs |
| cable pause | `logs/lanes/<lane>/` | `MMTS_PAUSE_DIR` |

Rules the page enforces: **one lane with HV at a time with the cable**, any
number with the Vitrek (biased together with `parallel_bias`, else taking turns); the
**12+12 probe runs alone** (it rewrites the link map every lane reads), and
**one lane per Kria** (one puller per Kria).

**Clear** (it was Destroy) stops the lane, drops payload power on its Kria,
ramps the HV off when the lane had it, ends the lane's own puller, and puts the
lane back to the start so it can be initialized again.

## HV off

Each lane's **HV** box decides. With it unticked the lane is exactly the Multi
Pedestal Run: `run_slots_hv.sh` hands over to task4's `run_slots.sh`, N
pedestals per slot under the plain label, and **nothing calls `hv.sh`**, not in
Run, Stop or Clear. Initialize never touches the Keithley; an HV run checks it
(`hv idn`) before anything is powered.

## HV on

Task4 run again at every bias voltage. Three hexaboards on one Kria through the
multiplexer board, **one slot at a time**, with one Keithley and one HV cable.
One press of Run does, for every slot that has a serial, in order A then B then C:

```
route the HV to the slot        cable moved by hand (a pause), or a Vitrek relay
run_slot.sh <S> .. <label>_gate 0     bring-up -> gate, no pedestal
hv.py on, hv.py leakcheck             abort the slot above maxLEAK below 500 V
for BV in biasVOLTS:
    hv.py set <BV>                    ramp, settle, read the leakage
    ped_run.sh <S> <nRUNS>            -> Mux<S>_<label>_BV<BV>/
    finder line, hexmaps, collect     -> DataLoc/daqplots/<runTAG>_BV<BV>/<S>-*.png
hv.py off                             ramp to 0, output off, before the next slot
```

Nothing about the DAQ is new. `run_slot.sh` and `ped_run.sh` on the bench are
untouched; the bias loop is a wrapper around them.

**`run_slot.sh` is called for the gate only (NRUNS 0), with no pedestal.**
Since 2026-11-20 the 0 V gate pedestal is skipped (it cost about 2 min per
slot). The **first bias point is now the stall check**: a wedged slot is found
after the HV has ramped, and its scan stops there. Every bias point goes
straight to `ped_run.sh`, which does **not** bring up, so the module keeps the
one bring-up that won its lottery for the whole scan. Put `0` in the bias list
if you want 0 V data.

**Run asks first that the LV is switched ON** (a pop-up on every Run and Run
all, HV or not), and with HV on, that the HV cable is on this bench.

# The instrument

**The bench Keithley IS the single-module stand's Keithley**, on pi0's only
serial adapter, `ASRL/dev/ttyUSB0::INSTR`. Consequences, all of them operational:

- the two stands cannot run HV at the same time;
- the HV cable moves between the benches by hand, exactly as it moves between
  mux slots, so **never start a run without knowing which bench the cable is on**;
- if pi0 is ever rebooted, check `/dev/serial/by-id/` before the next HV run: the
  `ttyUSB` numbering can swap. The by-id form is in the config as a comment.

`hv.py` on the client host is the only thing on this bench that talks to the
instrument, and `scripts/task5_hv/hv.sh` is the only thing that calls `hv.py`.
It runs from the single-module stand's GUI directory so it inherits that stand's
`configuration.yaml`: one source of truth for the resource, the terminal and the
polarity. Polarity is `Reverse` on both stands, which drives the Keithley to
**+BV**, and `hv.py` prints it in its banner on every command.

```bash
scripts/task5_hv/hv.sh idn        # instrument, resource, terminal, polarity, compliance
scripts/task5_hv/hv.sh set 300 --settle 5   # compliance defaults to 1050 uA
scripts/task5_hv/hv.sh off        # ramp to 0, output off
```

**Every `hv.py` call is a new process, and the driver's `__init__` sends
`*RST`, which drops the output with no ramp.** `set` deliberately leaves the bias
on for the pedestal run that follows, so `hv.py` walks a live output down to 0 V
over a raw session **before** the driver is constructed. That is also why a bare
`hv.py read` reports a zero-bias current: for leakage at a voltage use
`set <V>` or `read <V>`, both of which ramp, settle and read in one process. The
runner only ever uses `set`, whose reading is the leakage recorded for that point.

**No box, no interlock.** The single-module stand only enables HV with its box
closed. This bench has open HV leads: cover them.

**The compliance cannot be set low, and this is not a preference.**
`CurrentLimit` is 1.05 mA, the driver's own default and what the single-module
stand runs. A 2410 refuses a measurement range above the compliance range, and
`KeithleyPowerSupply` hardcodes the 100 µA range and switches up to 1 mA above
50 µA. A 10 µA compliance was tried on 2026-09-16: the range write was rejected
with error **824, "Cannot exceed compliance range"**, the reading was taken in an
undefined range state, and slot A reported **1.48 µA at 0 V** and aborted. At zero
bias there is no voltage to drive a current, so that number was never physical.
Protection against a short comes from the leakage abort at microamps, not from
the compliance.

**These modules have sensors**, so the leakage check is a real measurement.

**But this bench draws microamps at ZERO bias**, measured 2026-09-16 on slot A
with a clean instrument (1.05 mA compliance, no errors, source exactly 0.000 V):

| condition | current at 0 V |
|---|---|
| room lights on | 2.858 µA |
| room lights off, **but not fully dark** | 1.514 µA |

Stable to 0.1%, so both are real currents. A diode passes no leakage at zero
bias, so this is not leakage: it is **photocurrent**. These are large-area
silicon sensors on an open bench with no dark box, and turning the room lights
off removed 1.34 µA of it.

The second measurement was **not a true dark measurement**, so the 1.5 µA that
survived is most likely just the light that was left. It is not evidence of a
second effect, and nobody should go hunting one on the strength of it. **A proper
dark test has not been done yet**, and it is the first thing to do here: cover
the module opaquely and run `scripts/task5_hv/hv.sh read 0`. If that lands in the
nanoamps, light was the whole story.

Until then the single-module stand's 1 µA threshold is unreachable here, since
every slot aborted at the 0 V point before any bias was applied, so
`leak_abort_uA` is set to **1000 µA**. Be clear about what that costs: at 1 mA,
just below the 1.05 mA compliance, the check is a **short detector**, not a
sensor-quality check, and it will not catch a mildly leaky sensor. It is a form
field, so put it back to 1 µA as soon as a dark measurement supports it.

If a genuinely dark reading is still microamps, the next suspect is the module
being **powered** during the check (`kconn_pwr off`, then read 0 V again): every
reading so far was taken with the front-end live.

# How the HV reaches a slot

One config switch, `MMTS_bench.hv.switch`, also on the form. **The final
setup is `vitrek`**; `none` is for a bench without one.

| | `none` (cable) | `vitrek` (final) |
|---|---|---|
| cabling | one HV cable, moved by hand | one cable per module into a Vitrek 964i |
| Krias with HV | **one** | **any number**; biased together with `parallel_bias`, else they take turns |
| when the HV is routed | before the slot's bring-up (one cable move per slot) | after the slot's gate, so bring-ups never wait for the Keithley |
| between slots | ramp to 0, output off, **pause and ask**, Continue | ramp to 0, output off, every relay open, the next slot's relay |
| hardware | none | the Vitrek on the client host, beside the Keithley |

### The Vitrek

- **Relay map.** A lane is a tray row (K*n* = row *n*, or `hv_row` in
  `MMTS_bench.lanes`); its slots A/B/C are positions L/C/R, and the relay is
  `MMTS_channel_config.<row><L|C|R>.HVchannel` (1..24 as shipped). Configure
  prints each slot's relay, and the slot hint on the page shows it. Without a
  lane, the A/B/C entries (25..27) are used.
- **`$MM/vitrek.py`** on the client host is the only thing that talks to it
  (`idn`, `state`, `reset`, `route N`), with the serial settings of
  `MMTS_hardwares.vitek` (the key keeps its old spelling; `vitrek` also works).
  A route is reported ok only when `SYST?` reads back **exactly** that relay
  closed; anything else opens every relay and skips the slot's HV, so a failed
  relay can never label an unbiased module's pedestals with a voltage.
- The config says 9600 baud with `\n`, while the old driver class
  (`JobModule/device_VITREK_switch_control.py`) hardcodes 115200 with `\r` and
  never reads the config. `vitrek.py` uses the config. Run
  `hv_switch.py vitrek --idn` once on the real instrument and fix whichever is
  wrong. `turn_on_HV_switch.py` (task3) swallows errors and exits 0; it is not
  used here.

### One Keithley, several Krias

`hv_lock.sh` gives the Keithley to one lane and slot at a time (a mkdir lock,
`logs/hv_session.lock`, owner "LANE SLOT PID"). A slot that wants it shows
**waiting for the Keithley (held by S2 B)**; the page header shows the holder.
A lock whose run died is taken over. `MMTS_bench.hv.lock_timeout_s` (4 h) is how
long a slot waits before it gives up its HV phase.

**Stop and Clear never touch another lane's HV.** They go through
`hv_guard.sh`, which ramps down and opens the relays only when no other live
lane holds the Keithley, and holds the lock while it does. The run's own
`hv.py idn` check is skipped while another lane holds the Keithley, because idn
resets the instrument.

The pause shows as a yellow bar in the page with a **Continue** button, and is
also released by `make -f makefile_task5 continue`. It gives up after
`MMTS_bench.hv.pause_timeout_s` (an hour) and skips the slot. The Keithley is at
0 V with the output off the whole time it is showing.

### Pedestal trimming (on by default)

The single-module stand's procedure for a bolted or encapsulated module
(`TestingGUIBase.py`, `InteractionGUI.trim_pedestals`), per slot, with the HV
held, right after the leakage check:

```
ramp to trim_volts (300 V; the list's top if it stops lower)
1 untrimmed reference pedestal           -> Mux<S>_<label>_BV300/
trim_run.sh <S> Mux<S>_<label>_trim:
    pedestal_scan    trim_inv per channel   -> trimmed_pedestal.yaml
    vrefnoinv_scan   Noinv_vref per half    -> vrefnoinv.yaml
    vrefinv_scan     Inv_vref per half      -> vrefinv.yaml
    each fit merged (trim_merge.py) into <serial>/Mux<S>_<label>_trim/trimmed_config.yaml
for every entry of biasVOLTS, on the trimmed config -> Mux<S>_<label>_trimmed_BV<V>/
```

- **Names.** Trimmed data carries `_trimmed` (`MuxA_ped_trimmed_BV300`, gallery
  `run1_trimmed_BV300`); anything without it is untrimmed, as is all data from
  before trimming existed.
- **The trims must be on the chips.** A changed config reaches the ROCs only on
  the i2c-server's first good initialize, so the trimmed pedestals pass the
  trimmed config as `PED_BASECFG` and check the readback with `PED_EXPECT` (every
  per-half `Inv_vref`/`Noinv_vref`; the channel trims are not in the readback).
  A mismatch stops that slot's scan: "the trims did not reach the chips".
- **A failed trim is not fatal**: the scan runs untrimmed with the plain label,
  and the slot says TRIMMING FAILED. A failed reference pedestal stops the slot,
  as any failed pedestal does.
- The scans use `MMTS_L1A_LOG2PERIOD=10` like `pedestal_run.py` (they hardcoded
  0, which overruns this bench's readout); upstream behavior is unchanged.
- Parallel bias: the trim voltage is the round's first point; every lane trims
  its own module there, then the list follows.
- The analysis maps chip N to the N-th sorted `roc*` key: right for LD and HD
  Full, **not yet checked for HD Top and Bottom**.
- Off: untick "trim pedestals" (or `trimPEDS=0`, or `trim_pedestals: false`).
  About 3 minutes per module, measured on the Alabama bench 2026-08-29.

Tests: `multimodule/test_trim_merge.py`; the trim order in `test_hv_parallel.py`.

### Parallel bias: one Keithley biases every lane at once

`MMTS_bench.hv.parallel_bias: true` (Vitrek only; `hvParallel=1` on the make line also works)
changes the order. The lanes do each mux slot **together**: every lane brings up
and gates its slot A, they meet (`hv_parallel.py`, files under `logs/hv_parallel/`),
and the first lane on the roster leads:

```
per module, its relay alone:  HV on, leakage check, HV off    <- per-module number
sum of the passing modules:   must fit parallel_sum_uA, else the leakiest are left out
every module that is kept:    all relays closed together, HV on once
for BV in biasVOLTS:          ramp, read the TOTAL current
                              every lane takes its pedestals in parallel; wait for all
ramp to 0, output off, every relay open
```

then slot B on every lane, then slot C. Rules:

- **A slow lane is waited for `parallel_wait_s` (900 s)** after the first lane
  arrives, then the round starts without it; the late lane runs in a round of
  its own afterwards. A dead lane is never waited for.
- **Only the leader touches the Keithley and the Vitrek.** A follower's Stop
  leaves the bias alone (the guard sees the leader's lock); its module stays
  biased until the leader's round ends. **Stopping the leader ramps every module
  of the round down**; a follower's pedestals running at that moment are not
  counted.
- During the scan the Keithley reads the **sum** over the modules in parallel, and
  every lane's page shows that total. The per-module leakage is the check's.
- The compliance covers the sum, so it cannot protect a single module; a module
  that breaks down mid-scan pulls the voltage down for all of them.
- **The summed leakage must fit `parallel_sum_uA`** (empty = half the
  compliance). Each module's number is its largest leak-check reading; the
  leakiest modules are left out until the sum fits, and their lanes take no
  pedestals for that slot. A module without a reading counts as the leakiest.
  The leak check stops at its last volts, so above that the compliance is the
  only protection.
- The relays still move only with the output off.

Tests: `test_hv_parallel.py` (the meeting point with stand-in lanes, then two real
runners in a dry run: order of the relay and HV calls, followers never driving
the instruments, the slow-lane drop) and `test_vitrek.py` (`route-many`).

Before the first real in parallel run, check with the output OFF that the 964i
holds several relays closed: `vitrek.py route-many 19,22` then `vitrek.py state`.

**Never switch the Vitrek with the output on.** `hv_switch.py` is only ever
called after the ramp to 0 and the output off, in both modes; `vitrek.py`
cannot see the Keithley, so the runner's order is the protection.

Tests: `test_hv_lock.py` (two lanes never hold it at once, stale takeover, the
guard, the relay per row), `test_vitrek.py` beside `vitrek.py` (run by
`test_hv_cli.py`: readback, a deaf instrument, a stuck relay), and the Vitrek
part of `test_ui_flow_hv.py` (two HV lanes; gate, relay, HV on, HV off, relays
open, in that order).

# Commands

Every target takes `useHV=0|1` (default 1). The page runs them with the lane's
`MMTS_LANE`, `MMTS_KRIA_IP`, `MMTS_PULLER_PORT`, `MMTS_REGISTRY_NAME` and
`MMTS_PAUSE_DIR` in the environment; without them they behave as before, for one
Kria on 6001.

### make -f makefile_task5 initialize
With `useHV=0` (what the page runs), task4's `preflight.sh` only. With
`useHV=1`, task4's `preflight.sh` (client host stack, hexacontroller on 22, port 6001 free
or ours, one puller per Kria, `daqplots/` cleared) and then one more step: the
Keithley answers `*IDN?`, and its polarity is printed. A stale cable pause file
from a killed run is dropped here too. `hv.py idn` resets the instrument and
leaves the output **off** at 0 V, so it is safe in a read-only preflight.

### make -f makefile_task5 run
```bash
make -f makefile_task5 run \
    moduleIDA=320XHF2CXG00001 moduleIDC=320XLR4DQE00020 \
    nRUNS=5 label=ped runTAG=run1 \
    biasVOLTS=1,10,50,100,300,300,500 hvSwitch=none maxLEAK=1
```

**The leakage check is clamped to the bias list.** `leak_check_volts` is a
fixed config list (the single-module stand's `0 1 10 100 300`), and without the
clamp a scan of `biasVOLTS=1,10,50` still drove the module to 300 V during the
check. Any check point above the highest bias point is dropped, so `1,10,50`
checks at `0 1 10` and the full `1,10,100,300,500` is unchanged. You lose
nothing by it: the bias loop reads and records the leakage at every voltage it
actually uses, so the check is only a pre-flight screen. This matters on boards
with a humidity-driven breakdown, where an unclamped check aborts the slot at
100 V before a single bias point is measured.

**Skipping the leakage check.** Untick "leakage check" on the page (or
`leakCHECK=0`, or `leak_check: false` under `MMTS_bench.hv`) and no slot is
screened: in serial mode `hv.py leakcheck` is not called, in parallel mode the
leader skips the per-module checks and the summed-leakage budget, and every
module of the round is biased together. The bias loop has no leakage abort of
its own, so a short or a leaky sensor is then caught only by the Keithley
compliance (5.25 mA here, the whole round's in parallel). The run banner, each
slot's line and the Configure plan all say so. The leakage at every bias point
is still read and recorded.

`biasVOLTS` is validated **before anything is powered**, against two ceilings:
the instrument's `MMTS_hardwares.keithley.MaxVoltage` (800 V) and the geometry's
own, from `board_params.py` (600 V for LD, 800 V for HD). The form checks the
same two as the list is typed.

A voltage may repeat, e.g. `biasVOLTS=0,300,300`: every entry is its own step,
ramped and measured again. The repeat gets its own name, `BV300` the first time
and `BV300_2` the second (`_3` the third), in the run directory, the gallery
(`run1_BV300_2`) and the parallel-bias meeting point, so nothing is overwritten.
The hexmap archive files both under 300 V; the run time tells them apart.

Per-slot exit codes are `run_slot.sh`'s, reported as `########## A: EXIT n`. For
task5, exit 0 means the gate passed and the slot is ready for bias, not that the
campaign is done; 4 and 5 both mean **no HV was applied**.

### make -f makefile_task5 stop
With `MMTS_LANE` set, the client side ends only that lane's recorded session
plus the `pedestal_run.py`/`delay_scan.py` aimed at its Kria; with `useHV=0`
there is no `hv.sh` call at all. Otherwise, as below.

The HV comes down **first**: a killed job must not leave 500 V on a cable someone
is about to move, and `run_slots_hv.sh`'s own EXIT trap can only run while it is
still alive. Then the local make, the client host's `run_slots_hv.sh`,
`run_slot.sh`, `ped_run.sh`, `delay_scan.sh`, `pedestal_run.py`, then the Kria's
`up_verified.sh` and `mmts_bringup.sh`, and then `hv.py off` again. Every pattern
uses the `[p]kill` bracket. **Never `daq-client`**: on the lab computer that is
the other stand's service, and it is stopped with `systemctl`.

### make -f makefile_task5 destroy
The page's **Clear**. Stop, then `pkill zmq_server` and `sudo kconn_pwr off` on
the Kria, then (for a lane) its own puller, then the HV off once more when
`useHV=1`.

### make -f makefile_task5 continue
Releases the cable pause, the same as the page's Continue button.

### make -f makefile_task5 hvoff
Ramp to 0 and turn the output off, nothing else. The one to reach for when a run
was killed outside the GUI.

# Results

The `.root` files stay on the client host, under
`$RESULTS_DIR/<serial>/Mux<S>_<label>_BV<BV>/pedestal_run/run_<UTC>/`, one
directory per slot and bias point. `collect_plots.sh` copies each one's hexmaps
into `DataLoc/daqplots/<runTAG>_BV<BV>/`, so the Check dropdown gets one entry
per bias point and `app_daqsummary.py` needs no change: `run1_BV300` is just
another run directory.

The BV is in the hexmap **titles** as well, next to the serial, from the `BV\d+`
token in the DUT name. It is deliberately not in the png file names:
`collect_plots.sh` keys on `Mux<S>_adc_mean.png`, and the run directory already
carries the voltage.

The leakage at each bias point is in the run log as hv.py's
`HV set ok {"current_A": ...}` line, and beside the slot in the page.

# Rules the implementation must not lose

- HV only after the gate; HV to 0 and the output off before the next slot, before
  Stop kills anything, and in Clear.
- Never switch the Vitrek, and never ask anyone to touch a cable, with the output on.
- The ramp is the driver's 25 V / 0.5 s. Do not shortcut it, including on the way
  down: that is what `pre_ramp` is for.
- Compliance is set before the output goes on, every time.
- Polarity is a config value, read once, printed in the banner.
- `hv.py` is the only thing that talks to the Keithley; nothing else imports the
  driver.
- Stage banners, exit codes and hv.py's `HV <cmd> <status> {...}` lines are the
  progress API.

# Running it without a bench

`MMTS_DRYRUN=1` makes `on_client.sh` print every bench command instead of running
it, and makes the cable pause print its prompt and continue, so the whole job can
be walked on a laptop with no Keithley:

```bash
MMTS_DRYRUN=1 make -f makefile_task5 run moduleIDA=320XHF2CXG00001 biasVOLTS=0,300
```

Tests, none of which touch the bench or the instrument:

```bash
source .venv/bin/activate && source ./init_bash_vars.sh
python3 scripts/task5_hv/test_hv_cli.py        # hv.py on a fake driver, the pause, the bias list
python3 scripts/task5_hv/test_progress_hv.py   # a replayed run transcript
python3 scripts/task5_hv/test_ui_flow_hv.py    # all six buttons, and the ORDER of the HV calls
```

`test_ui_flow_hv.py` is the one that matters: it asserts gate before HV,
leakcheck before any bias point, and the HV down before Stop kills anything.

# Installation

Everything task4 needs (see `README.task4.md`), plus:

- `hv.py` on the client host, beside the other `$MM` bench scripts. The Mac
  mirror is `multimodule/hexactrl-sw/hexactrl-script/multimodule/hv.py`; pi0 has
  no gitlab access, so it is seeded by rsync from the Mac.
- `pyvisa` and `pyvisa-py` importable by the client host's `python3`
  (`MMTS_bench.hv.python` if it is not the default one).
- The single-module stand's GUI checked out at `MMTS_bench.hv.gui_dir`
  (`/home/hep/hgcal-module-testing-gui` on pi0), with **its** `configuration.yaml`
  and **its** `KeithleyPowerSupply.py`. Use pi0's copy, not upstream: it differs
  in the port settings (9600 8N1, `\r` termination, "UCSB HighBay").

# Still to do

- **Trim at 300 V** (phase 2): `pedestal_scan`, `vrefnoinv_scan`, `vrefinv_scan`
  through the mux path, their yaml outputs merged into a per-module trimmed
  config, then the bias list again tagged `trimmed300`. The scripts exist in
  `ROCv3-alper-dev/ctrl`; the work is the config merge, which `ExternalPC.outyaml`
  shows how the single-module stand does.
- **RH and T** in the run tag, as the single-module stand records them. Typed into
  the form, or omitted on this bench.
- **Database upload** per bias point, as for task4.
