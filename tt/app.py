from flask import Flask, jsonify, render_template
#from multiprocessing import Process, Value
from multiprocessing import Process, Manager, Value
import subprocess
import time
import os
import signal

app = Flask(__name__)

# Global variables
is_running = Value('i', 0)  # 1 = Task Running, 0 = Idle
process_pid = Value('i', 0)  # Stores the process PID for termination
# manager = Manager()
# is_running = manager.Value('i', 0)  # Shared variable (1 = Running, 0 = Idle)
# process_pid = manager.Value('i', 0)  # Store process PID

def run_bash_script(is_running, process_pid):
    """Executes a Bash script and captures stdout/stderr in real-time."""
    #bash_command = "for a in  {0..100}; do echo $a; sleep 1.0; done"
    bash_command = "echo aaa ; sleep 100 ; echo finished"

    print(f"[INFO] Running script in process {os.getpid()}")

    with is_running.get_lock():
        is_running.value = 1  # Mark task as running

    process = subprocess.Popen(
        bash_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True
    )

    # Store the PID for termination
    with process_pid.get_lock():
        process_pid.value = process.pid

    # Capture stdout & stderr
    for line in iter(process.stdout.readline, ''):
        print("[STDOUT]", line.strip())
    for line in iter(process.stderr.readline, ''):
        print("[STDERR]", line.strip())

    process.stdout.close()
    process.stderr.close()
    process.wait()

    print("[INFO] Task finished.")
    with is_running.get_lock():
        is_running.value = 0  # Mark task as finished

@app.route('/')
def home():
    """Render the HTML page with Start/Stop buttons."""
    return render_template("index.html")

@app.route('/start_task', methods=['POST'])
def start_task():
    """Starts the Bash script execution in a separate process."""
    with is_running.get_lock():
        if is_running.value == 1:
            return jsonify({"status": "rejected", "message": "Task is already running"}), 409

    # Start new process
    process = Process(target=run_bash_script, args=(is_running,process_pid))
    process.start()

    print(f'[value orig] is_running = {is_running.value}')
    print(f'[value orig] process_pid = {process_pid.value}')
    return jsonify({"status": "accepted", "message": "Task started"}), 200

@app.route('/stop_task', methods=['POST'])
def stop_task():
    """Terminates the running Bash script."""
    global is_running
    print(f'[value] is_running = {is_running.value}')
    print(f'[value] process_pid = {process_pid.value}')

    with is_running.get_lock():
        if is_running.value == 0:
            return jsonify({"status": "rejected", "message": "No running task"}), 409

    # Get the process PID
    with process_pid.get_lock():
        pid = process_pid.value
        print(f'[PID] Got pid = {pid}')

    if pid > 0:
        os.kill(pid, signal.SIGTERM)  # Send termination signal
        print(f"[INFO] Terminated process {pid}")

    with is_running.get_lock():
        is_running.value = 0  # Mark as stopped

    return jsonify({"status": "stopped", "message": "Task stopped"}), 200

@app.route('/status', methods=['GET'])
def check_status():
    """Check if the task is currently running."""
    with is_running.get_lock():
        if is_running.value == 1:
            return jsonify({"status": "busy", "message": "Task is running"}), 200
        else:
            return jsonify({"status": "idle", "message": "Server is idle"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
