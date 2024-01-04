pyvisa = USB - RS232 controller
socket = a command port


### To do
* [x] Dockerize
* [ ] Let code is able to receive oversized message.
* [ ] Check 127.0.0.1 changed or not once the computer reboot or activate this code on other computer.
* [ ] dockerfile cannot support 'ln -s'. Need to think another way for how to synchronize the configurations
* [ ] How to load new configuration into dockerized container

### Note to port
The socket opened a port 5000 recorded in python file. So you can access this code via 127.0.0.1:5000 while directly activating code with python. However, once you dockerize this code, the connection follows the port mapping at 'docker run -p new_port:5000'. The connection port becomes new_port instead of 5000.

