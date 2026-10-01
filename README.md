# Installations
Use mini conda handling the python libraries. Note that this GUI should be deployed on Linux.
We recommended you use SSH forward 
To install the dependency, you need to use the following commands:

## 1. Clone This Repository and external package
```
### clone this repository
git clone git@github.com:ltsai323/MultiModuleTeststandUI.git
if [ "$?" != 0 ] && echo "[ERROR - UnableToCloneMMTS] Failed to clone MMTS"

cd MultiModuleTeststandUI

### initialize this GUI
make -f makefile_initialize_this_GUI help
```

```
make -f makefile_initialize_this_GUI help

# Usage: make <command> [opts]
# 
# Commands:
# 
#   task1a_setup_andrewGUI  clone Andrew's GUI and edit configuration. If you installed andrewGUI, use andrewGUI_install_path to link folder. [andrewGUI_install_path=/some/path/to/hgcal-module-testing-gui]
#   task1b_create_daqclient_service  edit daq-client.service for using port 6002~6025. And put them into ~/.config/systemd/user/. Use `systemctl --user restart daq-client-port6001.service` to active service
#   task1c_create_output_folder  make directory from hgcal-module-testing-gui/configuration.yaml
#   task3a_clone_IVscan_codes  clone IV scan packages
#   task3b_create_mmts_configuration  create mmts_configuration
#   flaska_open_firewall_port5001  open firewall port 5001 such you can access server http://127.0.0.1:5001
#   flaskb_make_virtual_environment  create python virtual envuironment
#   flaskc_make_app_as_system_service  make this MultimoduleTeststandUI as a system service
#   help             Display this help
```

```
### all initialize actions
make -f makefile_initialize_this_GUI task1a_setup_andrewGUI  andrewGUI_install_path=/some/path/to/hgcal-module-testing-gui
make -f makefile_initialize_this_GUI task1b_create_daqclient_service
make -f makefile_initialize_this_GUI task1c_create_output_folder
make -f makefile_initialize_this_GUI task3a_clone_IVscan_codes
make -f makefile_initialize_this_GUI task3b_create_mmts_configuration
### Need to modify **data/mmts_configurations.yaml**, this yaml config file will be used in flask DAQ and `external_packages/HGCal_Module_Production_Toolkit` for Andrew's GUI.
make -f makefile_initialize_this_GUI flaska_open_firewall_port5001
make -f makefile_initialize_this_GUI flaskb_make_virtual_environment
make -f makefile_initialize_this_GUI flaskc_make_app_as_system_service
```


## 2.Configs in mmts_configurations.yaml

This section illustrates the configs used in `data/mmts_configurations.yaml`


### Global settings (Required)

[Inspectors](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L24-L29) provides default options on GUI. It is not a necessary option because you can enter other text in GUI for more flexibility.

[DB info](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L2-L5) are required settings for accessing [HGCDB](https://github.com/cmu-hgc-mac/HGC_DB_postgres/tree/main). Please following Sindhu's instruction for building this database and fill the connection information here.

### Andrew's single module electrics testing GUI

[DataLoc](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L6) are used to identify the output location of electric test.

[OtherSettings](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L1-L33) follows [Andrew's instructions](https://gitlab.cern.ch/acrobert/hgcal-module-testing-gui). Only used in pedestal run.

### MMTS channel config

[Positional config](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L35-L156) are not suggested for modifications.

[dictionary key like **1L**, **1C**](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L37) maps to moduleIDs position on webpage.

[HVchannel](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L38) maps to the channel number on Vitek 964i.

[Kria IP, puller port and type](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L39-L41) were used for multiple pedestal run. Currently it is disabled. No need to modify this.

### MMTS package path

[These paths](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L157-L159) could be modified if you installed requried package in computer. By default, you don't need to modify it when you follow the installation instructions.

### MMTS hardwares (Required)

[These RS232 configs](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L161-L169) sets the RS232 address of keithley and vitek 964i. The configs follows [Andrew's instructions](https://gitlab.cern.ch/acrobert/hgcal-module-testing-gui/-/blob/master/README.md?plain=1#L35-46).

### external URL (Required)

[These URL](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L170-L176) should be addressed to a grafana dashboard, these dashboard would be linked to MMTS GUI for environmental monitoring. If you didn't build any of grafana dashboard, here is the [suggested example](https://github.com/ltsai323/MultiModuleTeststandUI-dashboards).


### deprecated options

[inspector](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L177) is deprecated. it will be removed in furture.

### thermalcycle iterations

[These illustrations](https://github.com/ltsai323/MultiModuleTeststandUI/blob/main/data/mmts_configurations.yaml.default#L179-L186) are displayed on drop down menu in Single IV test panel. This config shows the filled iteration (key) in hgcdb and displayed text (value) on MMTS GUI. I suggest you to modify the illustration for better understanding.





# Update this GUI

```
make -f makefile_initialize_this_GUI updateGUI
systemctl restart MMTS.service
```

## Check and clean up the MMTS GUI logs
Open link [http://127.0.0.1:5001/logs](http://127.0.0.1:5001/logs) for viewing the log files.

```
make -f makefile_initialize_this_GUI clean_logs
```




# Run GUI
```
#!/usr/bin/env bash
source .venv/bin/activate
source ./init_bash_vars.sh
.venv/bin/python3 app.py
```
* then open the link [http://127.0.0.1:5001](http://127.0.0.1:5001)
* Get current configs: [http://127.0.0.1:5001/api/get_config](http://127.0.0.1:5001/api/get_config)
