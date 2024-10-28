
sudo firewall-cmd --reload
### for socket - CPU monitor
sudo firewall-cmd --zone=public --add-port=5423/tcp
### for flask
sudo firewall-cmd --zone=public --add-port=5000/tcp
