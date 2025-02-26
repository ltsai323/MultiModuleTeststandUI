

## jobfrag

Pack python functions to a job fragment.
Each job fragment inherits from **jobfrag_base**, which configures the common used functions for further usage.
The configured functions are

### **__init__(someARGs)**

The constructor should contains some argument for the usage.
Also, the developers should create a YAML file for the constructor.
Such as the arguments are stored in YAML file.

### **__del__()**

The destructor of the object.
I'll suggest you put **Stop()** function before destructor.
Once the **__del__()** is called, the software lost all configurations to the hardware.
So be sure current running should be stopped before calling destructor

### **Initialize()**


### **Configure(parDICT)**

### **Run()**

### **Stop()**




## JobOrganization

A JobOrganization provides function executed in the MMTS.
However, every joborganization should be packed into a class inherits in **joborganization_base**.
The developer should provide the defined functions: __init__(self, theDICT), __del__(), Initialize(), Configure(theDICT), Run() and Stop().
