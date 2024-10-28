### Command History

```#!/usr/bin/env sh
# Build docker image from current Dockerfile (Do it once)
sudo docker build -t postgresql_dec2023 .
# Activate a process from image postgresql_dec2023 and open port 5423@PC mapping to 5432@Dockerfile (Do it once).
#  -d: detach mode
#  -it: interactive mode. If there is no shell activated. You are not able to exit this process
sudo docker run -p 5423:5432 --name postsql_dec2023 -d postgresql_dec2023
# list all running processes.
#  -a: including stopped process.
sudo docker ps -a
# stop a process. if you cannot exit interactive mode from process. You would need to stop and restart this process.
sudo docker stop 69557927de34

sudo docker start 69557927de34 # or you can use container name
sudo docker restart 69557927de34 ## stop and start
```
