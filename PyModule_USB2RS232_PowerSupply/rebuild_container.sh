#!/usr/bin/env sh
sh stop_container.sh
sudo docker rmi pymodule-usbrs232-powersupply
sudo docker build -t  pymodule-usbrs232-powersupply .
