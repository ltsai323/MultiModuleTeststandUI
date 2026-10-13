if [[ -n "$(ss -H -ltn 'sport = :5001')" ]]; then
    echo "An application is listening on port 5001."
else
    echo "Nothing is listening on port 5001."
    sudo systemctl status firewalld ## check service is opened or not. use start and enable to make it run permanently
    #sudo firewall-cmd --zone=public --add-port=5001/tcp ### temporally open
    sudo firewall-cmd --zone=public --add-port=5001/tcp --permanent ### changed permanant
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-port ### it should show 5001/tcp
fi
