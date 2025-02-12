import jobfrag_base
import pyvisa
import time
from typing import TextIO, Dict, Any

class JobFrag(jobfrag_base.JobFragBase):
    def __init__(self, hostNAME: str, userNAME: str, privateKEYfile: str, timeOUT: float,
                 stdOUT: TextIO, stdERR: TextIO,
                 cmdTEMPLATEs: Dict[str, str], argCONFIGs: Dict[str, Any], argSETUPs: Dict[str, Any]):
        """
        Initialize the power switch control job.
        
        Args:
            hostNAME: RS232 port name (e.g., '/dev/ttyUSB0')
            userNAME: Not used for RS232 but kept for template consistency
            privateKEYfile: Not used for RS232 but kept for template consistency
            timeOUT: Communication timeout in seconds
            stdOUT: Standard output stream
            stdERR: Standard error stream
            cmdTEMPLATEs: Command templates for the switch
            argCONFIGs: Configuration parameters
            argSETUPs: Initial setup parameters
        """
        self.port = hostNAME
        self.timeout = timeOUT
        self.stdout = stdOUT
        self.stderr = stdERR
        self.cmd_templates = cmdTEMPLATEs
        self.configs = argCONFIGs
        self.setups = argSETUPs
        
        # RS232 connection objects
        self.rm = None
        self.device = None
        
        # State tracking
        self.is_initialized = False
        self.is_running = False

    def __del__(self):
        """Cleanup resources on object destruction"""
        self.Stop()
        if self.device:
            try:
                self.device.close()
            except:
                pass
        if self.rm:
            try:
                self.rm.close()
            except:
                pass

    def Initialize(self):
        """Initialize RS232 connection and configure device"""
        try:
            self.rm = pyvisa.ResourceManager()
            self.device = self.rm.open_resource(f'ASRL{self.port}::INSTR')
            
            # Configure RS232 parameters from setups
            self.device.baud_rate = self.setups.get('baud_rate', 9600)
            self.device.data_bits = self.setups.get('data_bits', 8)
            self.device.stop_bits = self.setups.get('stop_bits', pyvisa.constants.StopBits.one)
            self.device.parity = self.setups.get('parity', pyvisa.constants.Parity.none)
            self.device.timeout = int(self.timeout * 1000)  # Convert to milliseconds
            
            # Send any initialization commands
            init_cmd = self.cmd_templates.get('init')
            if init_cmd:
                self.device.write(init_cmd)
            
            self.is_initialized = True
            self.stdout.write("Power switch initialized successfully\n")
            return True
            
        except Exception as e:
            self.stderr.write(f"Initialization failed: {str(e)}\n")
            return False

    def Configure(self, updatedCONF: Dict[str, Any]) -> bool:
        """
        Update configuration parameters
        
        Args:
            updatedCONF: Dictionary containing updated parameters
        """
        try:
            # Update configurations
            self.configs.update(updatedCONF)
            
            # Apply any necessary configuration changes to the device
            if self.is_initialized and self.device:
                # Example: Update device timing parameters
                if 'cycle_duration' in updatedCONF:
                    # Apply new timing if needed
                    pass
                    
            self.stdout.write("Configuration updated successfully\n")
            return True
            
        except Exception as e:
            self.stderr.write(f"Configuration update failed: {str(e)}\n")
            return False

    def Run(self):
        """Execute the power switching operation"""
        if not self.is_initialized:
            self.stderr.write("Device not initialized\n")
            return False
            
        try:
            self.is_running = True
            
            # Get operation parameters from configs
            duration = self.configs.get('duration', 1.0)
            operation = self.configs.get('operation', 'on')  # 'on' or 'off'
            
            # Get command template
            cmd = self.cmd_templates.get(operation)
            if not cmd:
                raise ValueError(f"No command template for operation: {operation}")
            
            # Execute command
            self.device.write(cmd)
            
            # Wait for specified duration
            time.sleep(duration)
            
            # Execute opposite command if needed
            opposite_cmd = self.cmd_templates.get('off' if operation == 'on' else 'on')
            if opposite_cmd:
                self.device.write(opposite_cmd)
            
            self.stdout.write(f"Power {operation} cycle completed\n")
            self.is_running = False
            return True
            
        except Exception as e:
            self.stderr.write(f"Run operation failed: {str(e)}\n")
            self.is_running = False
            return False

    def Stop(self):
        """Stop any ongoing operation"""
        if self.is_running:
            try:
                # Send stop command if defined
                stop_cmd = self.cmd_templates.get('stop')
                if stop_cmd:
                    self.device.write(stop_cmd)
                
                self.is_running = False
                self.stdout.write("Operation stopped\n")
                return True
                
            except Exception as e:
                self.stderr.write(f"Stop operation failed: {str(e)}\n")
                return False
