#!/usr/bin/env python3
import threading
import time
def pack_function_to_bkg_exec(func, args:tuple=()):
    t = threading.Thread()
    t = threading.Thread(target=func,args=args)
    t.start()
    return t

def waiting_for_thread_finished(t):
    while t.is_alive():
        time.sleep(1.0)

def kill_thread(theTHREAD):
    pass
    
class ThreadingTools:
    def __init__(self, extFUNC):
        self.stopSIGNAL = threading.Event()
        #self.execTHREAD = threading.Thread(target=extFUNC, args=(self.stopSIGNAL))
        self.execTHREAD = threading.Thread(target=extFUNC, args=())
    def BkgRun(self):
        if self.execTHREAD.is_alive():
            print(f'[AlreadyRunning] ThreadingTools got a duplicated BkgRun() command. Ignore second command')
            return
        self.execTHREAD.start()
    def Stop(self):
        self.stopSIGNAL.set()
    def __del__(self):
        self.Stop()
        time.sleep(0.5)
