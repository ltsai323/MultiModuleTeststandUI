from abc import ABC, abstractmethod

class JobModule_base(ABC):
    '''
    Abstract base class requiring specific methods to be implemented by subclasses.

    Module classes are used to define a whole job.
    Loaded a lots of job instances and run them in parallel or sequential.
    Such as we can manage the scheduler to arrange the jobs.
    '''

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def __del__(self):
        pass

    @abstractmethod
    def Initialize(self):
        """
        Initialize resources or setup required for this object.

        You should check all used functionalities with very quick command.
        For example, if you want to use SSH connection and send commands.
        You need to check:
            * the server exists
            * you can login server
            * The used command exists (like python3)
            * Try to check environment like PATH / executables / dependencies
            * Try to access a simple script providing the functionality
        """
        pass

    @abstractmethod
    def Configure(self, updatedCONF:dict):
        """
        Configure parameters or settings.
        """
        pass
    @abstractmethod
    def show_configurations(self) -> dict:
        '''
        Showing all configurations required in this class
        '''
        pass

    @abstractmethod
    def Run(self):
        """
        Execute the main functionality of this object.
        """
        pass

    @abstractmethod
    def Stop(self):
        """
        Stop the execution and clean up resources if necessary.
        """
        pass
