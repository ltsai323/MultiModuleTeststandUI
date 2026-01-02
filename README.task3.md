# Task3 as IV scanning

### Initialize
Check the RS232 devices connected to computer or not.
Read `data/mmts_configurations.yaml`.
```
### used for run.IVscan.sh
RS232:
  switch_vitek: 'ASRL/dev/DAQrs232_HVswitch::INSTR'
  HV_keithley: 'ASRL/dev/DAQrs232_keithley::INSTR'
```


### Run
Despite from pedestal run, IV scan cannot be multithreaded. So `-jN` is forbidden.
Also 1+3 plots are generated at output directory **tmp_files/outs/**.
1. module based plot
2. Summary plots for room temperature / -40 and +20 for all historical modules.


### Stop
Reset the state of Keithley and HV switch

