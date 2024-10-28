# web GUI powered by flask
Webpage for control panel and parameter monitoring.
The control panel is used for sending commands and receiving error messages for each individual pythonized unit controller.
Also the parameter monitoring page provides some historical tendency plot for checking.



### About Port

```
#!/usr/bin/env sh
 > sudo docker run --name test-flask-app -p 5423:8888 test-flask-app

##  * Serving Flask app 'app.2'
##  * Debug mode: off
## WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
##  * Running on all addresses (0.0.0.0)
##  * Running on http://127.0.0.1:8888
##  * Running on http://172.17.0.1:8888
 ```
 Somehow I cannot use 127.0.0.1:8888 accessing the website inside docker ONLY.
 But I can use 172.17.0.2:8888 at the same computer. (Other computer is not able to access over this IP address)
 And 192.168.50.60:5423 is exposed on the LAN. Every computer is able to access it.
 (P.S. You need to use firewall-cmd open the port 5423 first)


```
#!/usr/bin/env sh
> ifconfig
docker0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.17.0.1  netmask 255.255.0.0  broadcast 172.17.255.255
        inet6 fe80::42:a2ff:fedd:e3d9  prefixlen 64  scopeid 0x20<link>
        ether 02:42:a2:dd:e3:d9  txqueuelen 0  (Ethernet)
        RX packets 15846  bytes 1008056 (984.4 KiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 23242  bytes 87923953 (83.8 MiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```
The LAN ip 172.17.0.1 is the LAN created in docker.
So once we opened a port on docker,
we can use 172.17.0.1 to use the port inside computer instead of open the port to parent LAN.
The 127.0.0.1 is the port inside computer, which is not accessable from container. So docker create a daughter level LAN inside computer to host these ports.





### To to 
- [x] Dockerize
- [x] Create first button sending command via socket.
- [ ] Create first message area receiving message via socket.
- [ ] Find a control panel HTML template and put it to flask.
- [ ] Create secondary webpage for mornitoring environments.
 - [ ] Decide the monitoring index for automator.
 - [ ] Decide where to put the morntoring index.

### Build log

```
#!/usr/bin/env sh
> sudo docker build -t test-flask-app . # build image from Dockerfile
echo sudo docker run --name test-flask-app -p 5423:8888 test-flask-app # build a container from image. And activate this container
```

Also, once the python module accomplished the dockerization, the connection port follows the assignment of 'docker run -p'
