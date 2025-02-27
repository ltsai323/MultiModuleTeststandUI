#!/usr/bin/env sh
if [ "$BASH_SCRIPT_FOLDER" == "" ]; then echo "[EnvironmentFailure] Required variable BASH_SCRIPT_FOLDER not set. Load use_python_lib.sh"; exit fi
source $BASH_SCRIPT_FOLDER/step0.functions.sh

exec_at_ctrlpc 'daq-client'
#ssh ctrlpc 'ls'

### errors
<<LISTED_OUTPUT_MESG
" SUC: daq-client already activated. I should ignore this message
terminate called after throwing an instance of 'zmq::error_t'
  what():  Address already in use
"

" SUC: return nothing if accessed
"
LISTED_OUTPUT_MESG
