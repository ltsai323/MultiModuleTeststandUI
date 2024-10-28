#!/usr/bin/env sh

# http://127.0.0.1:8888
#python3 app.button_send_cmd_via_socket.py
#sudo docker start -ai test-flask-app

#sudo docker build -t  webui_flask .

# http://192.168.50.60:7777
sudo docker run --name webui_flask -p 7777:8888 webui_flask
#sudo docker stop webui_flask
##sudo docker start webui_flask
#sudo docker rm webui_flask
