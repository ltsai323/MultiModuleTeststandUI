#!/usr/bin/env python3
class ServerStatus:
    startup = 'startup'
    initializing = 'initializing' # status when Init() is executing
    initialized = 'initialized' # status of Init() was executed

    configured = 'configured'

    running = 'running' # status of Run() is executing
    idle = 'idle' # status of Run() was executed
    stopping = 'stopping' # status of Stop() is executing
    stopped = 'stopped' # status of Stop() was executed
    destroying = 'destroying'
    destroyed = 'destroyed'
    error = 'error'



def server_is_runable(currentSTATUS, jobID:str):
    stat = currentSTATUS
    if jobID == "Init":
        return True if stat in [ 'startup', 'destroyed' ] else False
    if jobID == "Configure":
        return True if stat in [ 'initialized', 'stopped', 'idle' ] else False
    if jobID == "Run":
        return True if stat in [ 'configured' ] else False
    if jobID == "Stop":
        return True if stat in [ 'running' ] else False
    if jobID == "Destroy":
        return True if stat in [ 'error', 'initializing', 'initialized', 'configured', 'running', 'idle', 'stopping', 'stopped' ] else False
