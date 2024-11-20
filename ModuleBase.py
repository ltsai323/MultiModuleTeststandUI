
class ModuleBase:
    '''
    only define the structure.

    Module classes are used to define a whole job.
    Loaded a lots of job instances and run them in parallel or sequential.
    Such as we can manage the scheduler to arrange the jobs.
    '''
    def __init__(self):
        pass

    def Initialize(self):
        pass

    def Configure(self, updatedCONF:dict):
        pass

    def Run(self):
        pass

    def Stop(self):
        pass

    def Destroy(self):
        pass
