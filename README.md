## Installations
Use mini conda handling the python libraries.
To install the dependency, you need to use the following commands:
```
#!/usr/bin/env sh
conda config --append channels anaconda
conda config --append channels conda-forge

envNAME=myPython3p9
conda create --name $envNAME python=3.9
conda activate $envNAME
conda install flask flask-socketio requests sphinx paramiko pyvisa pyyaml flask-wtf myst-parser flask-cors
```

Or you can load the file `used_packages_conda.txt` for building dependencies.
```
#!/usr/bin/env sh
conda config --append channels anaconda
conda config --append channels conda-forge

envNAME=myPython3p9
conda create -n $envNAME --file used_packages_conda.txt 
conda activate $envNAME
```

## Run code
```
#!/usr/bin/env sh
python3 app.py
```
then open the link [http://127.0.0.1:5001](http://127.0.0.1:5001)

# Documents
https://hep1.phys.ntu.edu.tw/~ltsai/html/index.html

## File descriptions
### app.py

This is the main function that activates the whole flask server.
No any input arguments required. All configurations are put into app_actbtn.py and app_bkgrun.py
### app_actbtn.py

Store the button functions of the webpage.

### app_bkgrun.py

Tell flask server handling the background running jobs.
To prevent the whole webpage holding.
Developers should execute jobs in background instead of foreground.
Such as you need to handle the background threads using threading module.

### app_global_variables.py

The global variables used for Flask

### app_socketio.py

The socket connection make a communication between client and server frequently and efficiently.
A Flask Jsonify() is used to send a big message and socket is designed to send small message frequently.

### DebugManager.py

The message manager for debugging

### LoggingMgr.py

The message manager for logging. The screen output like "print()" should be replaced into  log.info(), log.warning(), log.error().
Check logging module in python for help

### WebStatus.py

store web status such as webpage can be reloaded

### jobfrag_base.py

An abstract class prepared for flask server. Every jobfrag should contain these functions.

### jobfrag_sshconn.pyinstance.

The basic function for ssh connection. This code should be directly tested and pack them into jobfrag.

### jobmodule_example.py

example code loads jobfrag and create it as a module being executed serially.

### jobmodule_example_2sshconnection.py

example code loads jobfrag and create it as a module being executed serially.

### jobmodule_single_module_pedestalrun_no_power_handling.py

example code loads jobfrag and create it as a module being executed serially.

### threading_tools.py



# To do list
## hi
* [ ] 


## Future features
* [ ] Handle multiple connections 

### Job Priority
* [ ] execute_job_from_queue() : reads priorities of activing jobs.
* [ ] AbleToAcceptNewJob() should be moved into job priority instead of True and False.
* [ ] AbltoToAcceptNewJob(): how do I put job priority into this function.
* [ ] Is job_priority able to be controlled from rs232.py code?
* [ ] AddJob() should accept job priority. Such that every job is able to check priority before execute.

