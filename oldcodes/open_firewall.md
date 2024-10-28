
* Open port 5423


```
sudo firewall-cmd --list-ports # listing opened walls
### use this command to open firewall.
sudo firewall-cmd --zone=public --add-port=5423/tcp --permanent # allow port 5423

### reload firewall. If 5423 is not permanent, it will be closed again.
sudo firewall-cmd --reload # Reload firewalld for changes to take effect

### make port permanent. Still opened after reload
sudo firewall-cmd --zone=public --add-port=5423/tcp --permanent # allow port 5423
```
