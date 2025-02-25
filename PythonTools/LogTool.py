#!/usr/bin/env python3
import sys
from io import StringIO

def err_capture(func):
    # Save the original sys.stderr
    original_stderr = sys.stderr

    # Redirect sys.stderr to a StringIO object
    sys.stderr = StringIO()

    # Print the message to sys.stderr
    print(message, file=sys.stderr)

    # Get the captured stderr as a string
    captured_stderr = sys.stderr.getvalue()

    # Restore the original sys.stderr
    sys.stderr = original_stderr

    # Print the captured stderr and use it as needed
    print('orig stderr:',captured_stderr, file=sys.stderr)
    print("Captured Stderr:", captured_stderr)
    return captured_stderr

def LOG(info,name,mesg):
    print(f'[{info} - LOG]({name}) {mesg}', file=sys.stderr)

def do_something():
    import time
    for idx in range(10):
        print(f'hii {idx}',file=sys.stderr)
        time.sleep(0.5)
if __name__ == "__main__":
    orig_err = sys.stderr
    orig_out = sys.stdout

    sys.stdout = StringIO()
    sys.stderr = StringIO()
    do_something()

    cap_out = sys.stdout.getvalue()
    cap_err = sys.stderr.getvalue()

    sys.stdout = orig_out
    sys.stderr = orig_err

    print('orig err ', cap_err)
    print('orig out ', cap_out)

