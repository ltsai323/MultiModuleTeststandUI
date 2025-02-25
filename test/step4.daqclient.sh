#!/usr/bin/env sh
source step0.functions.sh
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
