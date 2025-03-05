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
    def __init__(self, extFUNC, stopSIGNAL=threading.Event()):
        self.stopSIGNAL = stopSIGNAL
        self.execTHREAD = threading.Thread(target=extFUNC, args=(self.stopSIGNAL,))
        #self.execTHREAD = threading.Thread(target=extFUNC, args=())
    def BkgRun(self):
        if self.execTHREAD.is_alive():
            print(f'[AlreadyRunning] ThreadingTools got a duplicated BkgRun() command. Ignore second command')
            return
        self.execTHREAD.start()
    def Stop(self):
        self.stopSIGNAL.set()
    def IsRunning(self):
        return self.execTHREAD.is_alive()
    def __del__(self):
        self.Stop()
        time.sleep(0.5)
def testfunc_ThreadingTools():
    def exec_func(stopTRIG = threading.Event()):
        idx = 0
        terminate_loop = False
        while not stopTRIG.is_set():
            time.sleep(0.4)
            print(f'[exec_func] looping in {idx}')
            idx+=1

            if stopTRIG.is_set(): terminate_loop = True
            if idx > 20: break

            if terminate_loop: break
        print(f'[exec_func] looping ended')
    
    the_bkg_thread = ThreadingTools(exec_func)
    the_bkg_thread.BkgRun()
    
    time.sleep(5)
    print(f'[StopTrigger] STOP!!!!!!')
    the_bkg_thread.Stop()
    time.sleep(2)

    print(f'[Ended] Program finished')
    exit()

def testfunc_ThreadingTools_external_stop():
    def exec_func(stopTRIG = threading.Event()):
        idx = 0
        terminate_loop = False
        while not stopTRIG.is_set():
            time.sleep(0.4)
            print(f'[exec_func] looping in {idx}')
            idx+=1

            if stopTRIG.is_set(): terminate_loop = True
            if idx > 20: break

            if terminate_loop: break
        print(f'[exec_func] looping ended')
    
    new_stop = threading.Event()
    the_bkg_thread = ThreadingTools(exec_func, new_stop)
    the_bkg_thread.BkgRun()
    
    time.sleep(5)
    print(f'[StopTrigger] STOP!!!!!!')
    #the_bkg_thread.Stop()
    new_stop.set()
    time.sleep(2)

    print(f'[Ended] Program finished')
    exit()
if __name__ == "__main__":
    #testfunc_ThreadingTools()
    testfunc_ThreadingTools_external_stop()
