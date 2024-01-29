#!/usr/bin/env python3

CONNECT = '[>-EstablishConnect-<]'

CLOSE = '-CLOSE-' # use to close current socket connection to CommandPost
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

