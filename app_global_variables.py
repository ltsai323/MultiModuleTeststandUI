#!/usr/bin/env python3
import queue
import PythonTools.WebStatus
import logging
from threading import local

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

# Configure the logging

MESG_LOG = 'logging.getLogger("AppLogger")'
# MESG_LOG.log('hiii')
# MESG_LOG.warning('jjj')




class BasicConfig:
    DEBUG = True
    WEB_STAT = WebStatus.WebStatus()
    JOB_QUEUE = queue.Queue()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    MESG_LOG = logging.getLogger("AppLogger")
class TestConfig(BasicConfig):
    DEBUG = True
    WEB_STAT = WebStatus.WebStatus()
    JOB_QUEUE = queue.Queue()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    MESG_LOG = logging.getLogger("AppLogger")


# use app.config.from_object(TestConfig) to initialize the variables
