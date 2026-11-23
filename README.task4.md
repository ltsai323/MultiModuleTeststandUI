# Task4 as the Multi Pedestal Run

Three hexaboards on one Kria through the multiplexer board, measured **one slot
at a time**. This job mode drives the bench flow of `MMTS_MAC_INSTRUCTIONS.md`
from the GUI: one press of Run does, for every slot that has a serial, in order
A then B then C:

```
register_boards.py A=.. B=.. C=..                   once, before any bring-up
POWER=<..> SKIP_PROBE=1 run_slot.sh <S> <FAMILY> <BOARD> <NROCS> <label> <N>
    = bring-up -> gate -> N pedestals -> finder line -> hexmaps -> per-half check
collect the slot's hexmap PNGs into DataLoc/daqplots/<runTAG>/<S>-*.png
```

`run_slot.sh` on the bench already contains every rule the instructions insist
on (kill the stale i2c-server, up to 8 bring-ups, gate before pedestal, unit
test one pedestal before spending N, a fresh puller per run). Nothing here
re-implements any of it.

# Installation

## The client host

The **client host** owns `daq-client`, `unpack`, ROOT and the `$MM` bench
scripts, and it is the only machine that talks to the hexacontroller. In
production the GUI runs on it; during development it is a separate box reached
over ssh. One config section says which:

```yaml
MMTS_bench:
  client_host: 'hep@pi0.physics.ucsb.edu'   ### '' means: the GUI host is the client host
  client_shell: 'bash -lc'                  ### login shell, so the client's ~/.bashrc applies
  slots: [A, B, C]
  default_nruns: 5
  default_label: ped
  skip_probe: 1
```

Everything else in task4 goes through `scripts/task4_mmts_pedestal/on_client.sh`
and does not know whether the client host is remote. Moving the GUI onto the
bench machine is then `client_host: ''` and a `DataLoc`, nothing else.

The client host's own `~/.bashrc` supplies the site values (`MMTS_ROOT`,
`KRIA_IP`, `MM`, `SCRIPTS`, `HEXACTRL`, `MMTS_VENV`, `RESULTS_DIR`,
`GUI_HEXMAP`); instructions 0.5 has the block. Check the seam with:

```bash
scripts/task4_mmts_pedestal/on_client.sh 'echo $MMTS_ROOT; ls $MM/run_slot.sh'
```

An ssh `ControlMaster` entry for the client host is worth having: one slot can
spend ten minutes inside a single ssh call.

# Commands

### make -f makefile_task4 initialize
`preflight.sh`: read-only, no power, no bring-up. It stops on the first problem,
because each of these otherwise surfaces an hour later as a hung scan.

1. the client host has the bench stack and its site exports
2. the hexacontroller answers on port 22
3. **port 6001 on the client host is free or ours.** A live
   `daq-client.service` stops the job outright, whatever uid the GUI holds,
   before the uid test is even reached. On the UCSB lab computer that service
   is the single-module stand's puller, running as root, and `lib.sh`'s
   `puller_restart` kills `daq-client` **by name with no uid filter**: as `hep`
   that pkill merely fails and our own bind then fails too (every scan reports
   `no summary.json`), but run the GUI as root and the same line takes the
   other stand down mid-campaign. The fix is the operator's, and it is
   `sudo systemctl stop daq-client.service`, never `pkill`.
4. **one puller per Kria.** A second `daq-client` anywhere on the network takes
   half of every run and the symptom names nothing.
5. the GUI's `daqplots/` directory is cleared, so the result dropdown starts empty.

Not in initialize: `kconn_pwr on` (the bring-up cycles payload power itself) and
`findslot.py` (cheap, but the instructions say not to repeat it, and Initialize
gets pressed more than once).

### make -f makefile_task4 run
One process, slots in sequence. **Never `-j`**: there is one Kria, one
i2c-server, one daq-server, and exactly one slot holds the trigger claim at a
time. One slot failing does not stop the others.

```bash
make -f makefile_task4 run \
    moduleIDA=320XLF4CQH00443 moduleIDC=320XLR4DQE00020 \
    nRUNS=5 label=ped runTAG=run1
```

Optional per slot: `powerBoardA=auto|fitted|none`, and `skipPROBE=0` to measure
the link map instead of using the shipped one (it costs a bring-up).

Exit codes are `run_slot.sh`'s, reported per slot as `########## A: EXIT n`:
1 bring-up failed, 2 probe gave no summary, 3 registry or map refused, 4 gate
failed, 5 first pedestal stalled, 0 pedestals ran.

### make -f makefile_task4 stop
Reaches through: the local make, then the client host's `run_slot.sh`,
`ped_run.sh`, `delay_scan.sh`, `pedestal_run.py`, then the Kria's
`up_verified.sh` and `mmts_bringup.sh` (which loops for ten minutes on its own).
Every pattern uses the `[p]kill` bracket, or `pkill -f` matches the command line
carrying it. **Never `daq-client`**: on the lab computer that is the other
stand's service. Nothing needs restoring afterwards; the next bring-up restarts
daq-server and the puller.

### make -f makefile_task4 destroy
Stop, then `pkill zmq_server` and `sudo kconn_pwr off` on the Kria.

# Serial to bring-up parameters

Characters 5 and 6 of the serial decide everything (instructions 2.1). The table
lives in `scripts/task4_mmts_pedestal/board_params.py` and is served to the form
at `/task4/board_table`, so the page and the runner cannot disagree.

| chars 5-6 | type | FAMILY | `--board` | ROCs | power distribution board |
|---|---|---|---|---|---|
| LF | LD Full | `initLD-Full-3b` | `LD-Full` | 3 | **fitted** |
| L5 | LD Five | `initLD-Five-3b` | `LD-Five` | 3 | none |
| LL, LR | LD Left, Right | `initLD-Left-3b` | `LD-Semi` | 2 | none |
| LB, LT | LD Bottom, Top | `initLD-Bottom-3b` | `LD-Semi` | 2 | none |
| HF | HD Full | `initHD-Full-trophyV3` | `HD-Full` | 6 | **fitted** |
| HT | HD Top | `initHD-Top-trophyV3` | `HD-Top` | 3 | none |
| HB | HD Bottom | `initHD-Bottom-trophyV3` | `HD-Bottom` | 4 | not yet seen, assumed none |
| HL, HR | HD Semi | `initHD-Semi-trophyV3` | `HD-Semi` | 2 | not yet seen, assumed none |

The power column costs the most when misread: a module with the board fitted
and the flag missing is never powered and reads `no ROCs`. The form keeps a
per-slot override (auto / fitted / none) because the HB and HL/HR rows are
guesses, and Configure prints the decision for every slot before Run.

Serials reach the bench scripts uppercase, dashless and 15 characters: the `$MM`
scripts, `module_ids.json` and `hexmap_robust.py` all read characters 5 and 6
positionally.

```bash
scripts/task4_mmts_pedestal/board_params.py 320XLF4CQH00443
# initLD-Full-3b LD-Full 3 POWER=
```

# Results

The `.root` files stay on the client host, under
`$RESULTS_DIR/<serial>/Mux<S>_<label>/pedestal_run/run_<UTC>/`. `collect_plots.sh`
copies each slot's newest hexmaps back to `DataLoc/daqplots/<runTAG>/` as
`<S>-adc_mean.png`, `<S>-adc_stdd.png` and `<S>-robust.png`, which is what the
Check button's gallery serves. A slot whose bring-up failed simply has none.

# Running it without a bench

`MMTS_DRYRUN=1` makes `on_client.sh` print every bench command instead of
running it, so the whole job can be walked on a laptop:

```bash
MMTS_DRYRUN=1 make -f makefile_task4 run moduleIDA=320XLF4CQH00443 nRUNS=2
```

`LOG_LEVEL=DEBUG` (port 5005) makes every GUI button run `make -n` instead of
`make`, printing the command it would run into the log pane.

Tests, none of which touch the bench:

```bash
source .venv/bin/activate && source ./init_bash_vars.sh
python3 scripts/task4_mmts_pedestal/test_board_params.py     # the serial table
python3 scripts/task4_mmts_pedestal/test_progress_parser.py  # a replayed run transcript
python3 scripts/task4_mmts_pedestal/test_ui_flow.py          # all five buttons, MMTS_DRYRUN
```

# Progress in the page

The `##########` stage banners and the exit codes **are** the progress API.
`app_task4.py` parses those and nothing deeper: the bench scripts change, and a
parser that reads their internals goes stale silently. Each slot gets an LED
(queued gray, bring-up yellow, running green, done green, failed red) and a
stage line; the log pane shows the last 40 lines of output.

`scripts/task4_mmts_pedestal/fixtures/run_slots_transcript.txt` is a recorded
run kept as the parser's fixture. When a bench script changes its banners,
`test_progress_parser.py` is what tells you.
