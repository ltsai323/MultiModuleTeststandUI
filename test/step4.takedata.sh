#!/usr/bin/env sh
if [ "$BASH_SCRIPT_FOLDER" == "" ]; then echo "[EnvironmentFailure] Required variable BASH_SCRIPT_FOLDER not set. Load use_python_lib.sh"; exit; fi
source $BASH_SCRIPT_FOLDER/step0.functions.sh

echo 'step 4 running'
exec_at_ctrlpc 'cd /home/ntucms/electronic_test_kria/HD_bottom && python3 pedestal_run.py -i 192.168.50.180 -f initHD-bottom.yaml -d mytest -I && echo FINISHED'
echo 'step 4 running ENDED'

### errors
<<LISTED_OUTPUT_MESG
" ERROR - if nothing found in 20 second <- timeout TBD
"
LISTED_OUTPUT_MESG
