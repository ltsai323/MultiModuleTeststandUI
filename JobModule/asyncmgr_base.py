import asyncio
import weakref
import logging
from abc import ABC, abstractmethod

class AsyncManager(ABC):
    def __init__(self):
        weakref.finalize(self, self._cleanup) # add a weak reference to __del__()


    ### env setup ON
    @abstractmethod
    async def Initialize(self):
        raise NotImplementedError('Initialize() requires to be implemented.')

    ### env setup OFF
    @abstractmethod
    async def Destroy(self):
        raise NotImplementedError('Destroy() requires to be implemented.')

    @abstractmethod
    def Configure(self):
        raise NotImplementedError('Configure() requires to be implemented.')

    @abstractmethod
    def show_configurations(self) -> dict:
        '''
        Showing all configurations required in this class
        '''
        pass
    
    ### run stage ON
    @abstractmethod
    async def Run(self):
        raise NotImplementedError('Run() requires to be implemented.')


    ### run stage ON
    @abstractmethod
    async def Stop(self):
        raise NotImplementedError('Stop() requires to be implemented.')



    def _cleanup(self):
        """Cleans up when instance is deleted."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.Destroy())
            else:
                loop.run_until_complete(self.Destroy())
        except RuntimeError:
            pass # once event loop no more exist. Not to execute
            #asyncio.run( self.Destroy() )


    ### Do Destroy before delete instance
    def __del__(self):
        """Ensures cleanup when instance is deleted."""
        print('__del__() exec')
        try:
            self._cleanup()
        except Exception:
            pass  # Avoid any errors during deletion
