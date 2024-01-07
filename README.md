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

### To do list
* [ ] Create a general yaml file to define connection port and ip address.
 - 1st option: Create a connection_ID = PyModule001 for identify. And ROOT/general_configs/connections.yaml defines connection_ID and properties.
 - 2nd option: Create a ROOT/general_configs/connections.yaml and use 'ln -s' to force all modules sharing values.
* [ ] Think a method to tell dockerfile using ../tools packages.
