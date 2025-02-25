#!/usr/bin/env sh
source step0.functions.sh
exec_at_ctrlpc 'sh hii_run.sh'
#ssh ctrlpc 'ls'

### errors
<<LISTED_OUTPUT_MESG
" ERROR - if nothing found in 20 second <- timeout TBD
"
LISTED_OUTPUT_MESG
