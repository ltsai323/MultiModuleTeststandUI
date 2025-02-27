#!/usr/bin/env sh
function exec_at_kria() {
  cmd=$1
ssh -i /Users/noises/.ssh/hgcalMMTS root@192.168.50.180 $cmd
}
function exec_at_ctrlpc() {
  cmd=$1
ssh -i /Users/noises/.ssh/hgcalMMTS ntucms@192.168.50.144 $cmd
}
function the_exit() { echo "ERROR - "$1; exit 1; }

