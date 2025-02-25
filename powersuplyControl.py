import paramiko
import threading
import select
import time
import LoggingMgr
from pprint import pprint
import jobfrag_sshconn
import jobmodule_base
import pyvisa
import yaml  # New import for YAML parsing

DEBUG_MODE = True

class JobModulePowerSupply(jobmodule_base.JobModule_base):
    '''
    Power supply control module using PyVISA over SSH.
    This module initializes an SSH connection using jobfrag_sshconn and manages two power supplies via PyVISA.
    It allows configuring, running, and stopping the power supplies remotely.
    '''
    def __init__(self, config_file):
        self.rm = pyvisa.ResourceManager()
        # Load configuration from YAML file
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Extract settings for two power supplies
        self.resource1 = config['power_supply_1']['resource']
        self.voltage1 = config['power_supply_1']['voltage']
        self.resource2 = config['power_supply_2']['resource']
        self.voltage2 = config['power_supply_2']['voltage']
        
        self.power_supply1 = None
        self.power_supply2 = None

    def __del__(self):
        if self.power_supply1:
            self.power_supply1.close()
        if self.power_supply2:
            self.power_supply2.close()
        self.rm.close()

    def Initialize(self):
        '''
        Initializes the SSH connection and sets up the power supply resources.
        '''
        try:
            self.power_supply1 = self.rm.open_resource(self.resource1)
            self.power_supply2 = self.rm.open_resource(self.resource2)
            print("Power supply 1 initialized.")
            print("Power supply 2 initialized.")
        except pyvisa.VisaIOError as e:
            print(f"VISA initialization error: {e}")

    def Configure(self, updatedCONF: dict) -> bool:
        '''
        Configures the SSH connection with updated settings.
        '''
        return is_configured  # Note: is_configured is undefined, placeholder

    def show_configurations(self) -> dict:
        '''
        Returns the current SSH connection configurations.
        '''
        return {
            'power_supply_1': {'resource': self.resource1, 'voltage': self.voltage1},
            'power_supply_2': {'resource': self.resource2, 'voltage': self.voltage2}
        }

    def Run(self):
        '''
        Turns on both power supplies, sets their voltages, and continuously reads their current and voltage measurements every second.
        '''
        if self.power_supply1 and self.power_supply2:
            try:
                # Power Supply 1
                self.power_supply1.write('OUTPUT:STATE ON')
                self.power_supply1.write(f'VOLTAGE {self.voltage1}')
                print(f"Power supply 1 turned on and voltage set to {self.voltage1} V.")
                
                # Power Supply 2
                self.power_supply2.write('OUTPUT:STATE ON')
                self.power_supply2.write(f'VOLTAGE {self.voltage2}')
                print(f"Power supply 2 turned on and voltage set to {self.voltage2} V.")
                
                while True:
                    # Measurements for Power Supply 1
                    current1 = self.power_supply1.query_ascii_values('MEAS:CURR?')[0]
                    voltage_meas1 = self.power_supply1.query_ascii_values('MEAS:VOLT?')[0]
                    print(f'PS1 - Measured Voltage: {voltage_meas1} V, Measured Current: {current1} A')
                    
                    # Measurements for Power Supply 2
                    current2 = self.power_supply2.query_ascii_values('MEAS:CURR?')[0]
                    voltage_meas2 = self.power_supply2.query_ascii_values('MEAS:VOLT?')[0]
                    print(f'PS2 - Measured Voltage: {voltage_meas2} V, Measured Current: {current2} A')
                    
                    time.sleep(1)
            except pyvisa.VisaIOError as e:
                print(f"VISA communication error: {e}")

    def Stop(self):
        '''
        Turns off both power supplies and stops the SSH connection.
        '''
        if self.power_supply1:
            try:
                self.power_supply1.write('OUTPUT:STATE OFF')
                print("Power supply 1 turned off.")
            except pyvisa.VisaIOError as e:
                print(f"Error turning off power supply 1: {e}")
        if self.power_supply2:
            try:
                self.power_supply2.write('OUTPUT:STATE OFF')
                print("Power supply 2 turned off.")
            except pyvisa.VisaIOError as e:
                print(f"Error turning off power supply 2: {e}")

if __name__ == "__main__":
    '''
    Example of how to run the module with a YAML configuration file.
    '''
    # Specify the YAML config file
    config_file = "data/LV_power_supply_config.yaml"
    
    # Create instance with config file
    job_module = JobModulePowerSupply(config_file)
    
    job_module.Initialize()
    
    try:
        job_module.Run()
    except KeyboardInterrupt:
        print("Stopping power supplies...")
        job_module.Stop()

    del job_module
