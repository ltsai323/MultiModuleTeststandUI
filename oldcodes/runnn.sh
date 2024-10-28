pwd
source $PWD/use_python_lib.sh
python3 PyModule_SSH_connection/ssport2002.py PyModule_SSH_connection/config/sshconfigs.commanderPC.yaml 2>&1 > log_port2002_commandPC &
python3 PyModule_SSH_connection/ssport2001.py PyModule_SSH_connection/config/sshconfigs.commanderPC.daqClient.yaml 2>&1 > log_port2001_commandPC_DAQClient &
python3 PyModule_SSH_connection/ssport2000.py PyModule_SSH_connection/config/sshconfigs.hexacontroller.yaml 2>&1 > log_port2000_hexacontroller &
cd WebUI_Flask
python3 app.py


# note
## not able to kill python3 process.
## it seems to have strange behavour

