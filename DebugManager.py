#!/usr/bin/env python3
DEBUG_MODE = True
def BUG(*_args):
    if DEBUG_MODE:
        args = list(_args)
        latest_item = args.pop(-1)
        printed = False
        if isinstance(latest_item, list) or isinstance(latest_item, tuple):
            printed = True
            print(*args)
            for line in latest_item:
                print('  -> ',line)
        if isinstance(latest_item, dict):
            printed = True
            print(*args)
            for key,val in latest_item.items():
                print(f'  -> {key}: {val}')
        if not printed:
            print(*args, latest_item)
