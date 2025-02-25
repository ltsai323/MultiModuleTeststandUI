#!/usr/bin/env python3

CONNECT = '[>-EstablishConnect-<]'

### system commands
INIT        = '-INITIALIZE-'
CONNECT     = '-CONNECT-'
CONFIGURE   = '-CONFIGURE-'
START       = '-START-'
PAUSE       = '-PAUSE-'
STOP        = '-STOP-'
DESTROY     = '-DESTROY-'
SYST_CMD = {
    2:'-INITIALIZE-',
    3:'-CONNECT-',
    4:'-CONFIGURE-',
    5:'-START-',
    6:'-PAUSE-',
    7:'-STOP-',

    9:'-DESTROY-',
    }


#CLOSE = '-CLOSE-' # use to close current socket connection to CommandPost
SHUTDOWN = '-SHUTDOWN-' # use to shutdown the CommandPost socket connection and quit this program

FORCED_CLOSE_CURRENT_CONNECTION = '-FORCEDCLOSECURRENTCONNECTION-'

STAT__N_A         = (  1 ,'N/A') # Nothing
STAT__INITIALIZED = (  2 ,'PyModule Initialized') # Established socket communication to PyModule
STAT__CONNECTED   = (  3 ,'PyModule Connected to HW') # PyModule connected to hardware
STAT__CONFIGURED  = (  4 ,'YAML configuration accepted') # Configuration loaded
STAT__STARTED     = (  5 ,'Program activating') # Program is activated
STAT__PAUSED      = (  6 ,'Program paused')
STAT__STOPPED     = (  7 ,'Program stopped') # Program is stopped

STAT__ERROR       = (  0 ,'ERROR')
STAT__CONNL_LOST  = ( -1 ,'Connection Lost')

STATUS_DETAIL = {
     1 :'N/A', # Nothing
     2 :'PyModule Initialized', # Established socket communication to PyModule
     3 :'PyModule Connected to hardware', # PyModule connected to hardware
     4 :'Current configuration accepted', # Configuration loaded
     5 :'Program activating', # Program is activated
     6 :'Program paused',
     7 :'Program stopped', # Program is stopped

     9 :'PyModule Destroyed', # Disable the socket communication to PyModule
     0 :'ERROR',
    -1 :'Connection Lost',
    }

ACTION_AND_STATUS_POOL = {
        1: {'cmd':'INITIALIZE','desc': 'Action: Initialize PyModule',  'statuscode': 102},
        2: {'cmd':'CONNECT'   ,'desc': 'Action: Connect to Hardware',  'statuscode':103},
        3: {'cmd':'CONFIGURE' ,'desc': 'Action: Synchronize the Configuration',  'statuscode':104},
        4: {'cmd':'START'     ,'desc': 'Action: Start Data Taking',  'statuscode':105},
        5: {'cmd':'PAUSE'     ,'desc': 'Action: Pause the Data Taking', 'statuscode':106},
        6: {'cmd':'STOP'      ,'desc': 'Action: Stop the Data Taking', 'statuscode':107},
        9: {'cmd':'DESTROY'   ,'desc': 'Action: Destroy PyModule Socket Connection', 'statuscode': 101},

        11: {'cmd':'FORCEDCLOSECURRENTCONNECTION', 'desc': 'Action: Forced disable the connection from all client', 'statuscode': 102},
        12: {'cmd':'SHUTDOWN' ,'desc': 'Action: Shutdown the whole system. The PyModule services are removed from system.', 'statuscode': -103},


        100: {'stat':'TESTING'    ,'desc': 'Status: Testing something' },
        101: {'stat':'N_A'        ,'desc': 'Status: N/A' },
        102: {'stat':'INITIALIZED','desc': 'Status: PyModule Initialized' },
        103: {'stat':'CONNECTED'  ,'desc': 'Status: PyModule Connected to Hardware' },
        104: {'stat':'CONFIGURED' ,'desc': 'Status: Configuration Updated' },
        105: {'stat':'STARTED'    ,'desc': 'Status: Program is Running now' },
        106: {'stat':'PAUSED'     ,'desc': 'Status: Program Paused' },
        107: {'stat':'STOPPED'    ,'desc': 'Status: Program Stopped' },

        -101: {'stat':'ERROR' , 'desc':'Error'},
        -102: {'stat':'NOCONN', 'desc':'Connection Lost'},
        -103: {'stat':'POWEROFF', 'desc':'The whole system is no more activated'},

        #-999: {'stat':'UNDEFINED', 'desc':'Undefined Situation'},
        }
def get_action_from_cmd(theCMD:str) -> str:
    for action_id, details in ACTION_AND_STATUS_POOL.items():
        if 'cmd' in details and details['cmd'] == theCMD: return str(action_id)
    return theCMD # if the theCMD is not predefined, return original string
def get_action_from_status(theSTAT:str) -> str:
    for action_id, details in ACTION_AND_STATUS_POOL.items():
        if 'stat' in details and details['stat'] == theSTAT: return str(action_id)
    return theSTAT # if the theSTAT is not predefined, return original string
def get_status_message(statIDX:int) -> dict:
    statIdx = int(statIDX)
    return ACTION_AND_STATUS_POOL[statIdx] if hasattr(ACTION_AND_STATUS_POOL, statIdx) else {'stat':'statIDX not found', 'desc': f'get_status_message() : stat idx {statIDX} found in ACTION_AND_STATUS_POOL'}
#def get_cmd_name(cmdIDX:int) -> int:
def get_cmd_name(cmdIDX:str) -> str:
    cmdIdx = 0
    try:
        cmdIdx = int(cmdIDX)
    except ValueError:
        return cmdIDX

    if int(cmdIdx) in ACTION_AND_STATUS_POOL and 'cmd' in ACTION_AND_STATUS_POOL[cmdIdx]:
        return ACTION_AND_STATUS_POOL[cmdIdx]['cmd']
    return f'cmdIdxNotFound:{cmdIdx}' # if the theCMD is not predefined

def get_cmd_from_action(cmdIDX:str) -> str:
    cmdIdx = 0
    try:
        cmdIdx = int(cmdIDX)
    except ValueError:
        return cmdIDX # if it is not a int, return original command

    if int(cmdIdx) in ACTION_AND_STATUS_POOL and 'cmd' in ACTION_AND_STATUS_POOL[cmdIdx]:
        return ACTION_AND_STATUS_POOL[cmdIdx]['cmd']
    return f'cmdIdxNotFound:{cmdIdx}' # if the theCMD is not predefined
def get_status_from_action(statIDX:str) -> str:
    statIdx = 0
    try:
        statIdx = int(statIDX)
    except ValueError:
        return statIDX # if it is not a int, return original command

    if int(statIdx) in ACTION_AND_STATUS_POOL and 'stat' in ACTION_AND_STATUS_POOL[statIdx]:
        return ACTION_AND_STATUS_POOL[statIdx]['stat']
    return f'statIdxNotFound:{statIdx}' # if the theCMD is not predefined

def _INIT():
    return get_action_from_cmd('INITIALIZE')
def _CONNECT():
    return get_action_from_cmd('CONNECT')
def _CONFIGURE():
    return get_action_from_cmd('CONFIGURE')
def _START():
    return get_action_from_cmd('START')
def _PAUSE():
    return get_action_from_cmd('PAUSE')
def _STOP():
    return get_action_from_cmd('STOP')
def _DESTROY():
    return get_action_from_cmd('DESTROY')

def _FORCED_CLOSE_CURRENT_CONNECTION():
    return get_action_from_cmd('FORCEDCLOSECURRENTCONNECTION')
def _ERROR():
    return get_action_from_cmd('ERROR')
