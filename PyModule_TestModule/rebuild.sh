#!/usr/bin/env sh
sh refresh.sh
sudo docker rmi pymodule-testmodule
sudo docker build -t  pymodule-testmodule .

