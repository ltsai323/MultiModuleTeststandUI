#!/usr/bin/env sh

#python3 app.button_send_cmd_via_socket.py
#sudo docker start -ai test-flask-app

#sudo docker run --name webui_flask -p 7777:8888 webui_flask
sudo docker stop webui_flask
#sudo docker start webui_flask
sudo docker rm webui_flask
sudo docker build -t  webui_flask .
