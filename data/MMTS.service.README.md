# Put this reopsitory as a system service

```
chmod +x ../app.py
### edit path in `data/MMTS.service` and `data/MMTS.service.variables`
sudo mv MMTS.service /etc/systemd/system/

sudo cp MMTS.service /etc/systemd/system/
sudo systemctl reload-daemon
sudo systemctl start MMTS.service ### activate service
#sudo systemctl stop  MMTS.service ### stop service
#journalctl -u MMTS.service  ### check error messages
