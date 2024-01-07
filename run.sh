#!/usr/bin/env sh
function the_exit() { echo -e "\n\n----- ERROR -----\n$1\n\n"; exit(1); }

# activate docker
sudo systemctl start docker
## open firewall
sh buildPostgrSQLfromDOCKERfile/open_port.sh || the_exit "failed to open firewall"
## activate postgreSQL
#sh /activate_SQL.sh
#sh buildPostgrSQLfromDOCKERfile/activate_SQL.sh || the_exit "failed to activate postgreSQL"
## init flask
#conda activate python3p9 || the_exit "failed to load python3.9 environment from miniconda"
#python3 flaskUI/app.py || the_exit "failed to activate flask"
sudo docker start test-pymodule
sudo docker start test-flask-app

