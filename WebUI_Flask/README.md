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
##  * Running on http://172.17.0.2:8888
 ```
 Somehow I cannot use 127.0.0.1:8888 accessing the website inside docker ONLY.
 But I can use 172.17.0.2:8888 at the same computer. (Other computer is not able to access over this IP address)
 And 192.168.50.60:5423 is exposed on the LAN. Every computer is able to access it.
 (P.S. You need to use firewall-cmd open the port 5423 first)




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
