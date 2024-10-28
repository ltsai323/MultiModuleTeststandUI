### Job Priority
* [ ] execute_job_from_queue() : reads priorities of activing jobs.
* [ ] AbleToAcceptNewJob() should be moved into job priority instead of True and False.
* [ ] AbltoToAcceptNewJob(): how do I put job priority into this function.
* [ ] Is job_priority able to be controlled from rs232.py code?
* [ ] AddJob() should accept job priority. Such that every job is able to check priority before execute.

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
conda install flask flask-socketio requests sphinx paramiko pyvisa pyyaml flask-wtf myst-parser
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
## File descriptions
### aaa.py
### app.py
This is the main function that activates the whole flask server.
No any input arguments required. All configurations are put into app_actbtn.py and app_bkgrun.py
### app_actbtn.py

### app_bkgrun.py
### app_dynamic_form.py
### app_global_variables.py
### app_socketio.py
### a.py
### bashcmd.py
### ConfigHandler.py
### ConfigLoader.py
### DebugManager.py
### JobCMDPackManager.py
### JobCMDPack.py
### JobStatManager.py
### rs232cmder.py
### sshconn.py
### StageCMDManager.py



# To do list
## hi
* [ ] 


## Future features
* [ ] Handle multiple connections

