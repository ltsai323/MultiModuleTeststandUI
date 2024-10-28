#!/usr/bin/env python3
import queue

class GlobalVars:
    def __init__(self):
        self.cmders = {}
        #self.jobstat = {}

_VARS_ = GlobalVars()
_LOG_CENTER_ = queue.Queue()
_JOB_STAT_ = {}


