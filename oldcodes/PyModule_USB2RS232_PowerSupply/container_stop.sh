#!/usr/bin/env sh
#sudo docker run --name pymodule-usbrs232-powersupply -p 2000:1234 pymodule-usbrs232-powersupply
sudo docker stop pymodule-usbrs232-powersupply
#sudo docker start pymodule-usbrs232-powersupply
sudo docker rm pymodule-usbrs232-powersupply
