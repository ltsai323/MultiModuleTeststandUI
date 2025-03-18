import asyncio
import pyvisa
import time

class Vitrek964i:
    """
   Asyncio-based control class for Vitrek 964i High Voltage Switching System

    Provides methods to control relay banks and individual channels,
    query device status, and handle custom commands.
    """

    def __init__(self, resource_name, baud_rate=115200, timeout=5000):
        """
        Initialize the Vitrek 964i controller

        Args:
            resource_name: VISA resource name (e.g., "ASRL/dev/ttyUSB0::INSTR")
            baud_rate: Baud rate for serial communication (default: 115200)
            timeout: Timeout in milliseconds (default: 5000)
        """
        self.resource_name = resource_name
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.rm = pyvisa.ResourceManager()
        self.instrument = None

    async def connect(self) -> bool:
        """Connect to the Vitrek 964i device"""
        try:
            self.instrument = self.rm.open_resource(self.resource_name)

            # Configure serial parameters
            if self.resource_name.startswith("ASRL"):
                self.instrument.baud_rate = self.baud_rate
                self.instrument.data_bits = 8
                self.instrument.stop_bits = pyvisa.constants.StopBits.one
                self.instrument.parity = pyvisa.constants.Parity.none
                self.instrument.flow_control = 0  # No flow control
                self.instrument.write_termination = '\r'
                self.instrument.read_termination = '\r'
                self.instrument.timeout = self.timeout

            # Small delay to ensure connection is established
            await asyncio.sleep(0.5)

            print(f"Connected to Vitrek 964i at {self.resource_name}")
            return True

        except pyvisa.VisaIOError as e:
            print(f"VISA error connecting to Vitrek 964i: {e}")
            return False
        except Exception as e:
            print(f"Error connecting to Vitrek 964i: {e}")
            return False

    def disconnect(self):
        """Disconnect from the device and clean up resources"""
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        if hasattr(self, 'rm') and self.rm:
            self.rm.close()
        print("Disconnected from Vitrek 964i")

    async def reset(self):
        """Reset the device to default state (all relays open)"""
        await self._send_command("*RST")
        await asyncio.sleep(0.5)

    async def open_all_relays(self):
        """Open all relays in the device"""
        await self._send_command("OPEN ALL")
        await asyncio.sleep(0.5)

    async def set_bank_state(self, bank_number, hex_state):
        """
        Set the state of all relays in a specific bank

        Args:
            bank_number: Bank number (0-7)
            hex_state: Hexadecimal state value (0-255) as string or int
                       '0' means all relays open, 'FF' means all relays closed
        """
        # Convert to proper format if int is provided
        if isinstance(hex_state, int):
            hex_state = f"#h{hex_state:02X}"
        elif not hex_state.startswith("#h"):
            hex_state = f"#h{hex_state}"

        await self._send_command(f"BANK,{bank_number},{hex_state}")
        await asyncio.sleep(0.5)

    async def get_bank_state(self, bank_number) -> str:
        """Get the state of all relays in a specific bank"""
        response = await self._send_command(f"BANK?,{bank_number}", expect_response=True)
        return response

    async def set_relay_state(self, relay_number, state):
        """
        Set the state of a specific relay

        Args:
            relay_number: Relay number (1-64)
            state: True/False or "ON"/"OFF"
        """
        if isinstance(state, bool):
            state_str = "ON" if state else "OFF"
        else:
            state_str = state.upper()

        await self._send_command(f"RELAY,{relay_number},{state_str}")
        await asyncio.sleep(0.1)

    async def get_relay_state(self, relay_number):
        """
        Get the state of a specific relay

        Args:
            relay_number: Relay number (1-64)

        Returns:
            "ON" or "OFF"
        """
        response = await self._send_command(f"RELAY?,{relay_number}", expect_response=True)
        return response

    async def get_all_states(self):
        """
        Get the state of all relays in the system

        Returns:
            String with all banks' states in hexadecimal
        """
        response = await self._send_command("SYST?", expect_response=True)
        return response

    async def get_identity(self):
        """
        Get device identification

        Returns:
            Device identity string
        """
        response = await self._send_command("*IDN?", expect_response=True)
        return response

    async def execute_custom_command(self, command, expect_response=False):
        """
        Execute a custom command on the device

        Args:
            command: Custom command string to send
            expect_response: Whether to expect a response

        Returns:
            Response string if expect_response is True, None otherwise
        """
        return await self._send_command(command, expect_response)

    async def _send_command(self, command, expect_response=False):
        """
        Send a command to the Vitrek 964i

        Args:
            command: Command string to send
            expect_response: Whether to expect a response

        Returns:
            Response string if expect_response is True, None otherwise
        """
        if not self.instrument:
            raise RuntimeError("Not connected to Vitrek 964i")

        try:
            self.instrument.write(command)

            if expect_response:
                # Use asyncio.sleep instead of time.sleep
                await asyncio.sleep(0.2)  # Short delay before reading
                response = self.instrument.read()
                return response.strip()
            return None

        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            raise

    async def set_bank_all_on(self, bank_number):
        """
        Set all relays in a bank to ON state

        Args:
            bank_number: Bank number (0-3)
        """
        await self.set_bank_state(bank_number, "#hFF")

    async def set_bank_all_off(self, bank_number):
        """
        Set all relays in a bank to OFF state

        Args:
            bank_number: Bank number (0-3)
        """
        await self.set_bank_state(bank_number, "#h00")

    async def get_error_status(self):
        """
        Retrieve any error messages from the device

        Returns:
            Error message string, or "No errors" if none
        """
        try:
            response = await self._send_command("ERR?", expect_response=True)
            return response
        except Exception:
            return "Error status unavailable"

    async def get_relay_count(self, relay_number):
        """
        Get the operation count for a specific relay

        Args:
            relay_number: Relay number (1-64)

        Returns:
            Operation count as integer
        """
        response = await self._send_command(f"COUNT?,{relay_number}", expect_response=True)
        try:
            return int(response)
        except (ValueError, TypeError):
            print(f"Invalid count response: {response}")
            return -1

    async def send_batch_commands(self, commands, expect_response=False):
        """
        Send multiple commands as a single batch

        Args:
            commands: List of command strings to send
            expect_response: Whether to expect a response

        Returns:
            Response string if expect_response is True, None otherwise
        """
        # Join commands with semicolon separator
        batch_command = ";".join(commands)
        return await self._send_command(batch_command, expect_response)

    def is_connected(self):
        """
        Check if the connection to the device is still valid

        Returns:
            True if connected, False otherwise
        """
        if not self.instrument:
            return False

        try:
            # Try a simple command that should always succeed
            self.instrument.write("?")
            time.sleep(0.1)
            response = self.instrument.read()
            return response.strip() == "1"
        except Exception:
            return False

    async def set_timeout(self, timeout_ms):
        """
        Set a new timeout value for commands

        Args:
            timeout_ms: New timeout in milliseconds
        """
        self.timeout = timeout_ms
        if self.instrument:
            self.instrument.timeout = timeout_ms

async def main():
    """Comprehensive example usage of the Vitrek964i class with all methods"""
    # Create controller instance
    vitrek = Vitrek964i("ASRL/dev/ttyUSB0::INSTR")

    try:
        # Connect to the device
        if await vitrek.connect():
            print("\n===== BASIC DEVICE INFORMATION =====")
            # Get device identity
            identity = await vitrek.get_identity()
            print(f"Device identity: {identity}")

            # Reset device
            await vitrek.reset()
            print("Device reset completed")

            # Check if connected
            connected = vitrek.is_connected()
            print(f"Connected status: {connected}")

            print("\n===== ERROR STATUS CHECK =====")
            # Check for any errors
            error_status = await vitrek.get_error_status()
            print(f"Initial error status: {error_status}")

            print("\n===== BANK OPERATIONS =====")
            # Example: Set first four relays in bank 0 to closed (pattern 00001111)
            await vitrek.set_bank_state(0, "#h0F")
            print("Set bank 0 to state #h0F (00001111)")

            # Verify the state
            state = await vitrek.get_bank_state(0)
            print(f"Bank 0 state: {state}")

            # Set all relays in bank 1 to ON
            await vitrek.set_bank_all_on(1)
            print("Set all relays in bank 1 to ON")

            # Verify the state
            state = await vitrek.get_bank_state(1)
            print(f"Bank 1 state: {state}")

            # Set all relays in bank 1 to OFF
            await vitrek.set_bank_all_off(1)
            print("Set all relays in bank 1 to OFF")

            # Verify the state
            state = await vitrek.get_bank_state(1)
            print(f"Bank 1 state: {state}")

            print("\n===== INDIVIDUAL RELAY OPERATIONS =====")
            # Example: Turn on a single relay
            await vitrek.set_relay_state(5, "ON")
            print("Set relay 5 to ON")

            # Check the relay state
            relay_state = await vitrek.get_relay_state(5)
            print(f"Relay 5 state: {relay_state}")

            # Check relay operation count
            count = await vitrek.get_relay_count(5)
            print(f"Relay 5 operation count: {count}")

            print("\n===== SYSTEM STATUS =====")
            # Get all states
            all_states = await vitrek.get_all_states()
            print(f"All relay states: {all_states}")

            print("\n===== CUSTOM COMMANDS =====")
            # Example: Custom command
            print("Executing custom command: BANK,2,#h33")
            await vitrek.execute_custom_command("BANK,2,#h33")

            # Get updated bank state
            state = await vitrek.get_bank_state(2)
            print(f"Bank 2 state after custom command: {state}")

            print("\n===== BATCH COMMANDS =====")
            # Send multiple commands in a batch
            batch_commands = [
                "BANK,0,#h55",  # Set alternating pattern in bank 0
                "BANK,1,#hAA",  # Set opposite alternating pattern in bank 1
                "RELAY,32,ON"   # Turn on relay 32
            ]
            await vitrek.send_batch_commands(batch_commands)
            print("Batch commands executed")

            # Verify results
            state0 = await vitrek.get_bank_state(0)
            state1 = await vitrek.get_bank_state(1)
            state32 = await vitrek.get_relay_state(32)
            print(f"Bank 0 state after batch: {state0}")
            print(f"Bank 1 state after batch: {state1}")
            print(f"Relay 32 state after batch: {state32}")

            print("\n===== TIMEOUT ADJUSTMENT =====")
            # Test timeout adjustment
            print("Setting timeout to 10 seconds")
            await vitrek.set_timeout(10000)

            # Try operation with new timeout
            await vitrek.get_all_states()
            print("Operation with new timeout completed successfully")

            print("\n===== CLEANUP =====")
            # Open all relays before disconnecting
            await vitrek.open_all_relays()
            print("All relays opened")

            # Check for any errors at the end
            error_status = await vitrek.get_error_status()
            print(f"Final error status: {error_status}")

    except Exception as e:
        print(f"Error during operation: {e}")
    finally:
        # Always disconnect properly
        vitrek.disconnect()
        print("Test sequence completed")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
