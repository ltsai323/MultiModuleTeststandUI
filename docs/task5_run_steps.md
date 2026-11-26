# Task5 run steps (parallel bias)

What one Run does on the multi-module bench. Each shelf runs its own copy; the
shelves meet for the HV steps.

## Before the run

1. **Configure:** check the serials, board types and the bias list against the
   Keithley (800 V) and board (LD 600 V, HD 800 V) limits.
2. **Run:** confirm LV is on and the HV cable is on this bench.

## Per slot (A, then B, then C)

3. **Bring-up:** power, firmware reload, ROC enable, i2c-server and daq-server
   (up to 4 tries).
4. **Gate:** links must align and pass CRC, else no HV for this slot.
5. **Meet:** wait up to 15 min for the other shelves; the lowest shelf leads and
   alone drives the Keithley and the Vitrek.
6. **Leakage check, one module at a time** (optional): at 100 V and the top
   bias point, never above it. Above 1000 uA, the module is dropped.
7. **Leakage budget:** the sum must stay under half the compliance, else the
   leakiest modules are left out.
8. **All modules together:** every relay closed, HV on.
9. **Trimming** (optional): at 300 V, one untrimmed pedestal, then
   `pedestal_scan`, `vrefnoinv_scan`, `vrefinv_scan`.
10. **Bias list:** default `1,10,50,100,300,300,500`. At each point every shelf
    takes its pedestals (trimmed if step 9 ran), and the hexmaps go to the
    gallery.
11. **HV off:** ramp to 0 V, output off, relays open.

In short: bring-up, gate, leakage checks, HV on, trimming, then
1, 10, 50, 100, 300, 300, 500 V with pedestals at each, then HV off.
