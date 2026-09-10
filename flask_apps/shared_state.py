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



def ReadConfig(key):
    ''' return dictionary. Once no such key in CURRENT_CONFIG, put empty string to the value for preserving the dictionary content '''
    return CURRENT_CONFIG.get(key,'')
def ReadConfigs(keys):
    ''' return dictionary. Once no such key in CURRENT_CONFIG, put empty string to the value for preserving the dictionary content '''
    return { k:CURRENT_CONFIG.get(k,'') for k in keys }

def SetConfig(key,val):
    global CURRENT_CONFIG
    CURRENT_CONFIG[key] = val

def ClearConfig():
    global CURRENT_CONFIG
    CURRENT_CONFIG = {}


def GetAllModuleIDs(dictORlist:str):
    modulepos = [
        'moduleID1L',
        'moduleID1C',
        'moduleID1R',
        'moduleID2L',
        'moduleID2C',
        'moduleID2R',
        'moduleID3L',
        'moduleID3C',
        'moduleID3R',

        'moduleID4L',
        'moduleID4C',
        'moduleID4R',
        'moduleID5L',
        'moduleID5C',
        'moduleID5R',
        'moduleID6L',
        'moduleID6C',
        'moduleID6R',

        'moduleID7L',
        'moduleID7C',
        'moduleID7R',
        'moduleID8L',
        'moduleID8C',
        'moduleID8R',
        ]
    moduleIDs = ReadConfigs(modulepos)
    if dictORlist == 'dict':
        return { pos: moduleIDs[pos] for pos in modulepos if moduleIDs[pos] }
    if dictORlist == 'list':
        return [ moduleIDs[pos] for pos in modulepos if moduleIDs[pos] ]
    raise NotImplementedError(f'[InvalidOption] option dictORlist "{dictORlist}" is invalid.')

