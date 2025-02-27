#!/usr/bin/env python3
### general status definition
### only used for automator
N_A         = (0, 'N/A')
INITIALIZED = (1, 'GUI is communicating to PyModules')
CONNECTED   = (2, 'PyModules are connected to hardwares')
CONFIGURED  = (3, 'Configuration synchroized')
RINNING     = (4, 'Taking data')
PAUSED      = (5, 'Program paused')
FINISHED    = (6, 'Job finished')
DESTROYED   = (7, 'PyModules are safely closed.')

ERROR       = (-1, 'ERROR')
CONNL_LOST  = (-2, 'Connection Lost')

### running mesg
EXEC_INITIALING = (11,'GUI is trying to communicating with the PyModules')
EXEC_CONNECTING = (21,'PyModules are trying to connect hardwares.')
EXEC_CONFIGURING= (31,'Synchroizing configurations.')
EXEC_DESTROYING = (71,'Shut down the system.')

