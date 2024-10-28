import JobStatManager
import ConfigHandler
class JobCMDPack:
    def __init__(self, name:str, jobtype:str,
                 logQUEUE, loadedPARs:ConfigHandler.LoadedParameterFactory):
        self.name = name
        self.jobtype = jobtype
        self.log = logQUEUE
        self.loaded_pars = loadedPARs

    def execute(self, jobCMDpack, stageCMD) -> JobStatManager.JobStatMgr:
        return self.exec_func(jobCMDpack,stageCMD)

    def RecordLog(self, log:str):
        self.log.put( f'[{self.name}] {log}' )
    def RecordErr(self, log:str):
        self.log.put( f'[ERROR - {self.name}] {log}' )
    def GetLogQueue(self):
        return self.log
    def GetErrQueue(self):
        return self.log

    def GetParDict(self):
        return self.loaded_pars.GetParDict()
    def SetPar(self,key,val):
        return self.loaded_pars.SetPar(key,val)


