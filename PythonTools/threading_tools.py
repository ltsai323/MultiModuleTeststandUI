#!/usr/bin/env python3
import threading
def pack_function_to_bkg_exec(func, args:tuple=()):
    t = threading.Thread()
    t = threading.Thread(target=func,args=args)
    t.start()
    return t

def waiting_for_thread_finished(t):
    while t.is_alive():
        time.sleep(1.0)

