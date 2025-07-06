## Installations
Use mini conda handling the python libraries. Note that this GUI should be deployed on Linux.
We recommended you use SSH forward 
To install the dependency, you need to use the following commands:
```
#!/usr/bin/env sh
conda config --append channels anaconda
conda config --append channels conda-forge

envNAME=myPython3p9
conda create --name $envNAME python=3.9
conda activate $envNAME
conda install flask flask-socketio requests sphinx paramiko pyvisa pyvisa-py pyyaml flask-wtf myst-parser flask-cors
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

## Run GUI
```
#!/usr/bin/env sh
source ./use_python_lib.sh
python3 app.py
```
then open the link [http://127.0.0.1:5001](http://127.0.0.1:5001)


## GUI developing
### app.py
Which provided a entry webpage at [mainpage](http://127.0.0.1:5001) for selecting job mode.


### flask_apps/app_task2.py
Provide a sub webpage executing `make -f makefile_task2` with related option.
This job mode is to take pedestal run parallelly on modules.

Once the form was filled with hexaboard ID, there activated related position of kria.


## Directly run without GUI
The GUI execute commands in makefile. So use `make help` checking all related commands.

* `make -f makefile_task2 initialize`
* `make -f makefile_task2 run -j3`
* `make -f makefile_task2 stop`
* `make -f makefile_task2 destroy`


## DAQ steps
### step1 initialize
* Turn on kria power
* load all related kria firmwares
### step2 configure

### step3 run
Each single kria runs command. Note that pullerPort should be modified for assigning kria physically.

* reload kria status and activate daq-client at background
    - `ssh root@$kriaIP 'fw-loader load /opt/cms-hgcal-firmware/hgc-test-systems/hexaboard-hd-tester-v2p0-trophy-v2/'`
    - `ssh root@$kriaIP 'systemctl restart i2c-server.service && systemctl restart daq-server.service'`
    - `ssh root@$kriaIP 'systemctl status i2c-server.service && systemctl status daq-server.service'`
    - `sleep 0.5`
    - `./daq-client -p 6002 &`
* waiting for 8 seconds
* `python3 pedestal_run.py -i $kriaIP -f $yamlfile -d $moduleID -I --pullerPort=6002`

