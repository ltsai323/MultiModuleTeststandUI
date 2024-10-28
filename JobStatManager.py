#!/usr/bin/env python3
class JobStatMgr:
    def __init__(self):
        pass
    def terminate(self):
        raise NotImplementedError('class JobStat requires further implementation')
    def IsFinished(self):
        raise NotImplementedError('class JobStat requires further implementation')
    def AbleToAcceptNewJob(self):
        raise NotImplementedError('class JobStat requires further implementation')
class JobStatMgr_SequentialJob(JobStatMgr):
    def __init__(self):
        pass
    def AbleToAcceptNewJob(self):
        return self.IsFinished()
class JobStatMgr_BkgJobMonitor(JobStatMgr):
    def __init__(self):
        pass
    def AbleToAcceptNewJob(self):
        return True
