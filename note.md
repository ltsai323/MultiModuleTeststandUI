## forward secure IP through SSH port forwarding
ssh -L 8888:192.168.51.213:5000 user@192.168.50.213
## connect it in browser
http://localhost:8888/index.html
