#!/usr/bin/env python3
import JobCMDPackManager
import JobStatManager


class StageCMDMgr:
    def __init__(self, initFUNC, runFUNC, testFUNC, stopFUNC, destroyFUNC):
        self.init = initFUNC
        self.run = runFUNC
        self.test = testFUNC
        self.stop = stopFUNC
        self.destroy = destroyFUNC
    def Initialize(self, cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr):
        return self.init   (cmdPACK, jobSTAT)

    def Configure(self, cmdPACK:JobCMDPackManager.JobCMDPack, **configs):
        for key,val in configs.items():
            cmdPACK.SetPar(key,val)

    def Run(self, cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr):
        return self.run    (cmdPACK, jobSTAT)

    def Test(self, cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr):
        return self.test   (cmdPACK, jobSTAT)

    def Stop(self, cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr):
        return self.stop   (cmdPACK, jobSTAT)

    def Destroy(self, cmdPACK:JobCMDPackManager.JobCMDPack, jobSTAT:JobStatManager.JobStatMgr):
        return self.destroy(cmdPACK, jobSTAT)
