import asyncio
import pyvisa
import time
import argparse
from typing import List, Dict, Optional, Union, Tuple

class RS232Dev:
    """Base class for RS232 device communication"""
    def __init__(self, tag: str):
        """Initialize RS232 device
        
        Args:
            tag: A label for identifying this device instance
        """
        self.rm = pyvisa.ResourceManager()
        self.tag = tag
        self.task = None
        
    def __del__(self):
        """Clean up resources when object is destroyed"""
        if hasattr(self, 'rm'):
            self.rm.close()
    
    def set_task(self, task):
        """Set an async task for this device
        
        Args:
            task: The async task to set
        """
        self.task = task
        
    async def await_task(self):
        """Wait for the device's task to complete
        
        Use with "await device.await_task()" to wait for completion
        """
        if not hasattr(self, 'task') or self.task is None:
            return  # No task needs to wait
            
        if not self.task.done():
            print(f'[{self.tag} - Await] Waiting for task to complete')
            await self.task


class Vitrek964i:
    """Control class for Vitrek 964i High Voltage Switching System"""
    
    def __init__(self, resource_name: str, baud_rate: int = 9600, timeout: int = 2000):
        """Initialize the Vitrek 964i controller
        
        Args:
            resource_name: VISA resource name (e.g., "ASRL/dev/ttyUSB0::INSTR")
            baud_rate: Baud rate for serial communication
            timeout: Timeout in milliseconds
        """
        self.rm = pyvisa.ResourceManager()
        self.resource_name = resource_name
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.instrument = None
        
    def connect(self):
        """Connect to the Vitrek 964i device"""
        try:
            self.instrument = self.rm.open_resource(self.resource_name)
            self.instrument.baud_rate = self.baud_rate
            self.instrument.timeout = self.timeout
            
            # Some devices don't support the clear() operation
            # Commenting out to avoid VI_ERROR_NSUP_OPER
            # self.instrument.clear()
            
            # Instead, let's try to reset communication in a safer way
            try:
                # Send a simple command to test communication
                self.instrument.write("*RST")
                time.sleep(0.5)  # Give device time to process
            except Exception as e:
                print(f"Warning: Initial reset command failed: {e}")
            
            # Check if connected properly by requesting ID
            idn = self.get_identity()
            print(f"Connected to: {idn}")
            return True
        except pyvisa.VisaIOError as e:
            print(f"VISA connection error: {e}")
            return False
        except Exception as e:
            print(f"Error connecting to device: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from the device and clean up resources"""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        if hasattr(self, 'rm'):
            self.rm.close()
    
    def send_command(self, command: str) -> Optional[str]:
        """Send a command to the Vitrek 964i and return response if applicable
        
        Args:
            command: Command string to send
        
        Returns:
            Response string if command generates a response, None otherwise
        """
        try:
            if not self.instrument:
                print("Error: Not connected to instrument")
                return None
                
            # Send command
            self.instrument.write(command)
            
            # If command ends with ?, it's a query that expects a response
            if command.strip().endswith('?'):
                response = self.instrument.read().strip()
                return response
            return None
        except pyvisa.VisaIOError as e:
            print(f"VISA IO error when sending command '{command}': {e}")
            return None
        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            return None
    
    def get_identity(self) -> str:
        """Get the device identity information
        
        Returns:
            Identity string from the device
        """
        return self.send_command("*IDN?") or "Unknown device"
    
    def get_status(self) -> str:
        """Get device status
        
        Returns:
            Status information
        """
        return self.send_command("STAT?") or "Unknown status"
    
    def get_error(self) -> str:
        """Get last error message
        
        Returns:
            Error message from device
        """
        return self.send_command("ERR?") or "No error information"
    
    def reset(self):
        """Reset the device to default state"""
        self.send_command("*RST")
        
    def close_channel(self, channel: int):
        """Close a specific relay channel
        
        Args:
            channel: Channel number to close (1-64)
        """
        if 1 <= channel <= 64:
            self.send_command(f"CLOSE {channel}")
        else:
            print(f"Error: Invalid channel number {channel}. Must be between 1-64.")
    
    def open_channel(self, channel: int):
        """Open a specific relay channel
        
        Args:
            channel: Channel number to open (1-64)
        """
        if 1 <= channel <= 64:
            self.send_command(f"OPEN {channel}")
        else:
            print(f"Error: Invalid channel number {channel}. Must be between 1-64.")
    
    def open_all_channels(self):
        """Open all relay channels"""
        self.send_command("OPEN ALL")
    
    def get_channel_status(self, channel: int) -> bool:
        """Get the status of a specific channel
        
        Args:
            channel: Channel number to check (1-64)
            
        Returns:
            True if channel is closed, False if open or error
        """
        if 1 <= channel <= 64:
            response = self.send_command(f"STAT? {channel}")
            if response:
                # Parse the response - typically 0 for open, 1 for closed
                return response.strip() == "1"
        return False
    
    def configure_route(self, input_channel: int, output_channels: List[int]):
        """Configure a route between input channel and multiple output channels
        
        Args:
            input_channel: Input channel number
            output_channels: List of output channel numbers to connect to input
        """
        # First open all channels to clear previous configuration
        self.open_all_channels()
        
        # Then close specified channels to create the route
        self.close_channel(input_channel)
        for out_ch in output_channels:
            self.close_channel(out_ch)


async def test_switching(resource_name: str):
    """Test the basic switching functionality of Vitrek 964i
    
    Args:
        resource_name: VISA resource name for the device
    """
    vitrek = Vitrek964i(resource_name)
    
    try:
        # Connect to the device
        if not vitrek.connect():
            print("Failed to connect to Vitrek 964i")
            return
            
        # Reset the device
        print("Resetting device...")
        vitrek.reset()
        await asyncio.sleep(1)
        
        # Get device information
        print("\nDevice Information:")
        print(f"Identity: {vitrek.get_identity()}")
        print(f"Status: {vitrek.get_status()}")
        
        # Test opening all channels
        print("\nOpening all channels...")
        vitrek.open_all_channels()
        await asyncio.sleep(1)
        
        # Test closing and opening specific channels
        for channel in [1, 5, 10]:
            print(f"\nTesting channel {channel}:")
            
            print(f"  Closing channel {channel}...")
            vitrek.close_channel(channel)
            await asyncio.sleep(0.5)
            
            status = vitrek.get_channel_status(channel)
            print(f"  Channel {channel} status: {'Closed' if status else 'Open'}")
            
            print(f"  Opening channel {channel}...")
            vitrek.open_channel(channel)
            await asyncio.sleep(0.5)
            
            status = vitrek.get_channel_status(channel)
            print(f"  Channel {channel} status: {'Closed' if status else 'Open'}")
        
        # Test routing configuration
        print("\nTesting routing configuration...")
        input_ch = 1
        output_chs = [5, 10, 15]
        print(f"  Configuring route from input {input_ch} to outputs {output_chs}")
        vitrek.configure_route(input_ch, output_chs)
        await asyncio.sleep(1)
        
        # Check status of configured channels
        print("  Checking configured channels:")
        channels_to_check = [input_ch] + output_chs
        for ch in channels_to_check:
            status = vitrek.get_channel_status(ch)
            print(f"  Channel {ch} status: {'Closed' if status else 'Open'}")
        
        # Clean up - open all channels
        print("\nCleanup: Opening all channels...")
        vitrek.open_all_channels()
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Always disconnect properly
        vitrek.disconnect()
        print("\nDisconnected from Vitrek 964i")


async def setup_vitrek_964i(tag: str, resource: str, setup_type: str) -> RS232Dev:
    """Setup and configure the Vitrek 964i with specified parameters
    
    Args:
        tag: An identifier for this device instance
        resource: VISA resource string for the device
        setup_type: Type of setup to perform (e.g., 'configure_channels', 'reset')
    
    Returns:
        RS232Dev instance representing the connection
    """
    # Define possible setup configurations
    configurations = {
        'reset': [
            '*RST',  # Reset device
            'OPEN ALL'  # Open all channels
        ],
        'configure_ch1_5': [
            'OPEN ALL',  # First open all
            'CLOSE 1',   # Close channel 1 (input)
            'CLOSE 5'    # Close channel 5 (output)
        ],
        'configure_ch1_10_15': [
            'OPEN ALL',
            'CLOSE 1',    # Close channel 1 (input)
            'CLOSE 10',   # Close channel 10 (output)
            'CLOSE 15'    # Close channel 15 (output)
        ],
        'open_all': [
            'OPEN ALL'    # Open all channels
        ]
    }
    
    # Check if setup type is valid
    if setup_type not in configurations:
        valid_configs = ', '.join(configurations.keys())
        raise KeyError(f'Invalid setup type "{setup_type}". Available options: {valid_configs}')
    
    # Create RS232 device
    rs232 = RS232Dev(tag)
    
    try:
        # Open connection to the device
        instr = rs232.rm.open_resource(resource)
        # Set communication parameters
        instr.baud_rate = 9600
        instr.timeout = 2000  # 2 seconds timeout
        
        # Execute the commands for the specified setup
        cmds = configurations[setup_type]
        for cmd in cmds:
            instr.write(cmd)
            # Allow a short delay between commands
            await asyncio.sleep(0.1)
        
        # Additional delay to ensure commands are processed
        await asyncio.sleep(0.5)
        
        return rs232
    except pyvisa.VisaIOError as e:
        print(f"VISA error: {e}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise


def initialize_device(device_address: str) -> bool:
    """Check if device is available and functioning
    
    Args:
        device_address: VISA resource address string
        
    Returns:
        True if device is available, False otherwise
    """
    try:
        rm = pyvisa.ResourceManager()
        # Get list of available resources for debugging
        resources = rm.list_resources()
        print(f"Available VISA resources: {resources}")
        
        # Try opening the resource
        print(f"Attempting to connect to: {device_address}")
        instr = rm.open_resource(device_address)
        
        # Configure serial parameters if it's a serial device
        if device_address.startswith("ASRL"):
            print("Configuring as serial device...")
            instr.baud_rate = 9600
            instr.data_bits = 8
            instr.stop_bits = pyvisa.constants.StopBits.one
            instr.parity = pyvisa.constants.Parity.none
            instr.flow_control = pyvisa.constants.VI_ASRL_FLOW_NONE
            instr.timeout = 2000  # 2 seconds
        
        # Try to get device identity with error handling
        try:
            print("Sending IDN query...")
            instr.write("*IDN?")
            idn = instr.read().strip()
            print(f"Device identified as: {idn}")
        except Exception as query_error:
            print(f"IDN query failed: {query_error}")
            # If IDN query fails, try a simple command without expecting response
            try:
                print("Trying simple reset command...")
                instr.write("*RST")
                time.sleep(0.5)
                print("Reset command sent successfully")
            except Exception as cmd_error:
                print(f"Basic command also failed: {cmd_error}")
        
        # Close the resource manager
        instr.close()
        rm.close()
        return True
    except pyvisa.VisaIOError as e:
        print(f"VISA error: Unable to connect to device at {device_address}")
        print(f"Error details: {e}")
        
        # Provide troubleshooting steps based on error
        if "VI_ERROR_NSUP_OPER" in str(e):
            print("\nTroubleshooting suggestions:")
            print("1. This error often means the operation is not supported by the device")
            print("2. Check if the device address format is correct")
            print("3. For serial devices, try using a simpler format like 'ASRL1::INSTR' or '/dev/ttyUSB0'")
            print("4. Make sure you have proper permissions to access the device")
        
        return False
    except Exception as e:
        print(f"Error initializing device: {e}")
        return False


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Control Vitrek 964i High Voltage Switching System')
    parser.add_argument('--device', type=str, default="ASRL/dev/ttyUSB0::INSTR",
                        help='VISA resource name (default: ASRL/dev/ttyUSB0::INSTR)')
    parser.add_argument('--action', type=str, choices=['test', 'reset', 'config1', 'config2', 'open_all', 'list'],
                        default='test', help='Action to perform')
    parser.add_argument('--direct', action='store_true',
                        help='Use direct device name (e.g., /dev/ttyUSB0 instead of ASRL/dev/ttyUSB0::INSTR)')
    
    args = parser.parse_args()
    
    # Handle 'list' action to list available resources
    if args.action == 'list':
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            print("\nAvailable VISA resources:")
            for i, res in enumerate(resources):
                print(f"{i+1}. {res}")
            print("\nTo use a specific resource, run with --device option")
            rm.close()
            exit(0)
        except Exception as e:
            print(f"Error listing resources: {e}")
            exit(1)
    
    # Adjust device format if direct option is used
    device_addr = args.device
    if args.direct and not device_addr.startswith("ASRL"):
        if device_addr.startswith("/dev/"):
            # Convert /dev/ttyUSB0 to ASRL/dev/ttyUSB0::INSTR
            device_addr = f"ASRL{device_addr}::INSTR"
        else:
            # Handle COM ports on Windows
            device_addr = f"ASRL{device_addr}::INSTR"
        print(f"Using VISA resource: {device_addr}")
    
    # Check if device is available
    if not initialize_device(device_addr):
        print(f"\nDevice not available at {device_addr}")
        print("\nTroubleshooting tips:")
        print("1. Try using the --list action to see available devices")
        print("2. Check your serial port name/number")
        print("3. For serial devices, try using the --direct option with a path like '/dev/ttyUSB0'")
        print("4. Ensure you have permission to access the port (may require sudo on Linux)")
        print("5. Check that the device is powered on and properly connected")
        exit(1)
    
    # Perform requested action
    if args.action == 'test':
        # Run the test suite
        asyncio.run(test_switching(device_addr))
    else:
        # Map action to setup_type
        action_map = {
            'reset': 'reset',
            'config1': 'configure_ch1_5',
            'config2': 'configure_ch1_10_15',
            'open_all': 'open_all'
        }
        
        # Execute the corresponding setup
        try:
            rs232_dev = asyncio.run(setup_vitrek_964i('vitrek', device_addr, action_map[args.action]))
            print(f"Successfully executed action: {args.action}")
        except Exception as e:
            print(f"Failed to execute action {args.action}: {e}")
