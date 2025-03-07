import asyncio
import multiprocessing
import signal
import logging
import os
async def background_task():
    """A long-running async job"""
    print(f"Background job started with PID {os.getpid()}...")
    try:
        while True:
            print("Running async job...")
            await asyncio.sleep(0.5)  # Simulating work
    except asyncio.CancelledError:
        print("Background job was cancelled.")
async def background_task_0():
    """A long-running async job"""
    print(f"Background job started with PID {os.getpid()}...")
    idx = 6
    try:
        while idx:
            idx -= 1
            print("000 Running async job...")
            await asyncio.sleep(1.0)  # Simulating work
    except asyncio.CancelledError:
        print("Background job was cancelled.")

def run_async_job():
    """Run asyncio job in a separate process"""
    asyncio.run(background_task())

async def testfunc():
    task1 = asyncio.create_task(background_task())
    task2 = asyncio.create_task(background_task_0())
    await task2
    print('task2 finished!. Sleeping for 3 second and returned. (task1 should be keep running but program ended. So you will see the task1 also finished. Indeed, it is not ended')
    await asyncio.sleep(3)
    return task1

if __name__ == "__main__":
    asyncio.run(testfunc())

