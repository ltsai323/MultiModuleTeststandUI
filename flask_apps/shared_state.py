#!/usr/bin/env python3
import threading


jobmode = ''
threading_lock = threading.Lock()
# threading_lock.acquire()
# threading_lock.release()
server_status = 'startup'
debug_mode = False
#job_stop_flag - threading.Event()
#job_thread = {'thread': None}
CURRENT_CONFIG = {}


runidx = 0 ## used to identify run tag. It is always increased

DAQresult_current_modified = '' ## recorded state of os.path.getmtime(dirDAQresult)



def ReadConfig(keys):
    ''' return dictionary. Once no such key in CURRENT_CONFIG, put empty string to the value for preserving the dictionary content '''
    return { k:CURRENT_CONFIG.get(k,'') for k in keys }

def SetConfig(key,val):
    global CURRENT_CONFIG
    CURRENT_CONFIG[key] = val

def ClearConfig():
    global CURRENT_CONFIG
    CURRENT_CONFIG = {}
