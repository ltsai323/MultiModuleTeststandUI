#!/usr/bin/env sh
#sudo docker run --name pymodule-testmodule -p 2001:2000 pymodule-testmodule
sudo docker stop pymodule-testmodule
#sudo docker start pymodule-testmodule
sudo docker rm pymodule-testmodule
#sudo docker rmi pymodule-testmodule
#sudo docker build -t  pymodule-testmodule .
