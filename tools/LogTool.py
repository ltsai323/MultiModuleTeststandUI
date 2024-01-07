#!/usr/bin/env python3
import sys
def LOG(info,name,mesg):
    print(f'[{info} - LOG]({name}) {mesg}', file=sys.stderr)

