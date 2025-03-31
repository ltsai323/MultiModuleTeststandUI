import pyvisa
import time

def test_vitrek_command_variations(resource_name):
    """Test different variations of commands for Vitrek 964i"""
    rm = pyvisa.ResourceManager()
    
    try:
        print(f"Attempting to connect to: {resource_name}")
        instr = rm.open_resource(resource_name)
        
        # Configure serial parameters
        if resource_name.startswith("ASRL"):
            instr.baud_rate = 115200
            instr.data_bits = 8
            instr.stop_bits = pyvisa.constants.StopBits.one
            instr.parity = pyvisa.constants.Parity.none
            instr.flow_control = 0  # No flow control
            instr.write_termination = '\r'
            instr.read_termination = '\r'
            instr.timeout = 5000
            
        print("Connection established.")
        
        # Reset the device first
        print("\nResetting device...")
        instr.write("*RST")
        time.sleep(3)
        
        # Try different command variations
        command_variations = [
            "BANK,0,#h0F",    # Manual's #h format with uppercase F
            "BANK,1,#h11",    # Manual's #h format with uppercase F
            "BANK,2,#h31",    # Manual's #h format with uppercase F
        ]
        
        for cmd in command_variations:
            print(f"\nTrying command variation: {cmd}")
            try:
                instr.write(cmd)
                time.sleep(1)

                idx = cmd.split(',')[1]
                
                # Check the bank state
                instr.write(f"BANK?,{idx}")
                time.sleep(0.5)
                response = instr.read()
                print(f"Bank {idx} state after command: {response}")
                
                # If successful, break out of the loop
                if response.strip() == cmd.split(',')[-1]:
                    print("Success! Command accepted correctly.")
                    
            except Exception as e:
                print(f"Error with command '{cmd}': {e}")
        
        # Final check of all relay states
        try:
            instr.write("SYST?")
            time.sleep(0.5)
            status = instr.read()
            print(f"\nFinal relay states: {status}")
        except Exception as e:
            print(f"Error reading system state: {e}")
            
        print("\nTest completed.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'instr' in locals():
            instr.close()
        rm.close()

# Run the test with your device address
test_vitrek_command_variations("ASRL/dev/ttyUSB0::INSTR")
