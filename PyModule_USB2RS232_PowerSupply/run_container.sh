#!/usr/bin/env sh
#sudo docker build -t  pymodule-usbrs232-powersupply .
sudo docker run --device=/dev/ttyUSB0 --name pymodule-usbrs232-powersupply -p 2235:2234 pymodule-usbrs232-powersupply python server.py device:/dev/ttypUSB0
#sudo docker run --device=/dev/ttyUSB1 --name pymodule-usbrs232-powersupply -p 2235:2000 pymodule-usbrs232-powersupply python server.py
#sudo docker run --name pymodule-usbrs232-powersupply -p 2235:2234 pymodule-usbrs232-powersupply
#sudo docker stop pymodule-usbrs232-powersupply
##sudo docker start pymodule-usbrs232-powersupply
#sudo docker rm pymodule-usbrs232-powersupply
