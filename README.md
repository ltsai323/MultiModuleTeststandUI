# Multimodule Teststand Controller
24 modules IV testing at the same time will be required for HGCal production.
This repository aims to control every individual equipment at one control panel.

This is separated into three parts : webUI, database and unit commander.
### WebUI
Based on Flask, providing buttons sending command to unit commander and message boxes receiving messages.
Also another webpage loading historical information drawing line charts provides information to environmental parameters.
As the user, webUI is the only thing been touched.
### Database
The mini database receives every readout from unit commander.
### Unit commander
Unit commander directly communicates with equipment like power supply via USB port / RS232 port / ethernet port.
Yaml configuration files records every parameter used in the code.
Very few parameters would be modified from WebUI to simplify complexity during operation.



## Note for developing
### Special words inside the MesgHub.MesgUnit
The status "JOB_FINISHED" and "ERROR FOUND" are used for identify to ended the socket.recv() inside CommandPost/new_structure.SendLongCMD()

### Update socketio.emit() while the long job
Add additional socketio.sleep(0.03) inside CommandPost/new_structure.SendLongCMD() to force Flask flash its emit buffer. Such as the webpage is able to update the current stdout from PyModule. [Reference](https://blog.csdn.net/wangyuehy/article/details/123382520)

### Ignore further messages if "JOB_FINISHED" or "ERROR FOUND" received while executing CommandPost/new_structure.SendLongCMD()

### Every loaded PyModule is stored insde WebUI_Flask/app_actbtn._VARS_
This is a global variable storing all variables. This is a dirty writing method but I don't know how to pass the argument into flask. Flask also need to search for the listed pymodule inside _VARS_

### Every action is designed as a job to a job queue. All of jobs are put into a queue except for Initialize.
The job will be put into queue and execute piece by piece. So initialize button is not able to press twice and need additional time delay


### To do list
* [ ] Create a general yaml file to define connection port and ip address.
 - 1st option: Create a connection_ID = PyModule001 for identify. And ROOT/general_configs/connections.yaml defines connection_ID and properties.
 - 2nd option: Create a ROOT/general_configs/connections.yaml and use 'ln -s' to force all modules sharing values.
* [ ] Think a method to tell dockerfile using ../tools packages.
