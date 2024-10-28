#!/usr/bin/env sh
#sudo docker build -t  pymodule-testmodule .
sudo docker run --name pymodule-testmodule -p 2001:2000 pymodule-testmodule python server.py hi jjj
#sudo docker run --name pymodule-testmodule -p 2235:2234 pymodule-testmodule
#sudo docker stop pymodule-testmodule
##sudo docker start pymodule-testmodule
#sudo docker rm pymodule-testmodule
