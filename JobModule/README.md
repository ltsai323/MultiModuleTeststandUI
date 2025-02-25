JobModule is modules used in JobOrganizer
A JobModule provides function executed in the MMTS.
However, every jobmodule should be packed into a class inherits in jobmodule_base.
The developer should provide the defined functions: __init__(self, theDICT), __del__(), Initialize(), Configure(theDICT), Run() and Stop().
