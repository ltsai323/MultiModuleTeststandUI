import paramiko
import threading
import select
import time
import PythonTools.LoggingMgr as LogginsMgr
from pprint import pprint
#import jobfrag_sshconn
#import jobmodule_base
import JobModule.jobfrag_sshconn as jobfrag_sshconn 
import JobModule.jobmodule_base  as jobmodule_base
import pyvisa

DEBUG_MODE = True

class JobModulePowerSupply(jobmodule_base.JobModule_base):
    '''
    Power supply control module using PyVISA over SSH.
    This module initializes an SSH connection using jobfrag_sshconn and manages a power supply via PyVISA.
    It allows configuring, running, and stopping the power supply remotely.
    '''
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.resource = 'ASRL/dev/ttyUSB0::INSTR'  # Replace with actual VISA resource string
        self.power_supply = None

    def __del__(self):
        if self.power_supply:
            self.power_supply.close()
        self.rm.close()

    def Initialize(self):
        '''
        Initializes the SSH connection and sets up the power supply resource.
        '''
        try:
            self.power_supply = self.rm.open_resource(self.resource)
            print("Power supply initialized.")
        except pyvisa.VisaIOError as e:
            print(f"VISA initialization error: {e}")

    def Configure(self, updatedCONF: dict) -> bool:
        '''
        Configures the SSH connection with updated settings.
        '''
        return is_configured

    def show_configurations(self) -> dict:
        '''
        Returns the current SSH connection configurations.
        '''
        return {}

    def Run(self):
        '''
        Turns on the power supply, sets the voltage, and continuously reads the current and voltage measurements every second.
        '''
        if self.power_supply:
            try:
                self.power_supply.write('OUTPUT:STATE ON')
                voltage = 1.5  # Set desired voltage
                self.power_supply.write(f'VOLTAGE {voltage}')
                print("Power supply turned on and voltage set.")
                
                while True:
                    current = self.power_supply.query_ascii_values('MEAS:CURR?')[0]
                    voltage_meas = self.power_supply.query_ascii_values('MEAS:VOLT?')[0]
                    print(f'Measured Voltage: {voltage_meas} V, Measured Current: {current} A')
                    time.sleep(1)
            except pyvisa.VisaIOError as e:
                print(f"VISA communication error: {e}")

    def Stop(self):
        '''
        Turns off the power supply and stops the SSH connection.
        '''
        if self.power_supply:
            try:
                self.power_supply.write('OUTPUT:STATE OFF')
                print("Power supply turned off.")
            except pyvisa.VisaIOError as e:
                print(f"Error turning off power supply: {e}")

if __name__ == "__main__":
    '''
    Example of how to run the module.
    '''
    
    job_module = JobModulePowerSupply()
    
    job_module.Initialize()
    
    try:
        job_module.Run()
    except KeyboardInterrupt:
        print("Stopping power supply...")
        job_module.Stop()

    del job_module
