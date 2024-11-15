#!/usr/bin/env python3
import queue
import WebStatus

class GlobalVars:
    def __init__(self):
        self.cmders = {}
        #self.jobstat = {}

### old variables
_VARS_ = GlobalVars()
_LOG_CENTER_ = queue.Queue()
_JOB_STAT_ = {}

### new variable
DEBUG = 'False'
WEB_STAT = 'WebStatus.WebStatus()'
JOB_QUEUE = 'queue.Queue()'




class BasicConfig:
    DEBUG = True
    WEB_STAT = WebStatus.WebStatus()
    JOB_QUEUE = queue.Queue()
class TestConfig(BasicConfig):
    DEBUG = True
    WEB_STAT = WebStatus.WebStatus()
    JOB_QUEUE = queue.Queue()

# use app.config.from_object(TestConfig) to initialize the variables
