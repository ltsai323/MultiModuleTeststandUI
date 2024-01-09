#!/usr/bin/env sh
sh container_stop.sh
cd ..
sudo docker rmi pymodule-testmodule
sudo docker build -t  pymodule-testmodule -f PyModule_TestModule/Dockerfile .

