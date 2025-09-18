#!/usr/bin/env python3
import threading


jobmode = ''
threading_lock = threading.Lock()
# threading_lock.acquire()
# threading_lock.release()
server_status = 'startup'
#job_stop_flag - threading.Event()
#job_thread = {'thread': None}

next_runtag = '' ## run tag used in `make run runTAG=next_runtag`

DAQresult_current_modified = '' ## recorded state of os.path.getmtime(dirDAQresult)
