#!/usr/bin/env sh
function exec_at_kria() {
  cmd=$1
#ssh -i /Users/noises/.ssh/hgcalMMTS root@192.168.50.180 $cmd
ssh -i /home/ntucms/.ssh/HGCtrler_key_kria root@192.168.50.180 $cmd
}
function exec_at_ctrlpc() {
  cmd=$1
#ssh -i /Users/noises/.ssh/hgcalMMTS ntucms@192.168.50.144 $cmd
eval $cmd
}
function the_exit() { echo "ERROR - "$1; exit 1; }

#exec_at_ctrlpc "echo hiii jjj"
