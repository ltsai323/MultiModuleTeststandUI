#!/usr/bin/env sh
sh container_stop.sh

cd ..
sudo docker rmi pymodule-usbrs232-powersupply
sudo docker build -t  pymodule-usbrs232-powersupply -f PyModule_USB2RS232_PowerSupply/Dockerfile .
