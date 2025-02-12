import sys
from switch_control import JobFrag  # Replace with your actual module name

def test_power_switch():
    # Basic command templates
    cmd_templates = {
        'init': '*RST',      # Reset command (modify based on your switch)
        'on': 'ON',          # ON command
        'off': 'OFF',        # OFF command
        'stop': 'ABORT'      # Stop command
    }

    # Basic configuration
    arg_configs = {
        'duration': 2.0,     # 2 seconds duration
        'operation': 'on'    # Default operation
    }

    # RS232 setup parameters
    arg_setups = {
        'baud_rate': 9600,
        'data_bits': 8,
        'parity': 'none',
        'stop_bits': 1
    }

    # Create JobFrag instance
    job = JobFrag(
        hostNAME='/dev/ttyUSB0',  # Change to your port
        userNAME='',              # Not used for RS232
        privateKEYfile='',        # Not used for RS232
        timeOUT=1.0,
        stdOUT=sys.stdout,
        stdERR=sys.stderr,
        cmdTEMPLATEs=cmd_templates,
        argCONFIGs=arg_configs,
        argSETUPs=arg_setups
    )

    # Test sequence
    print("Initializing...")
    if job.Initialize():
        print("Initialization successful")

        # Test configuration update
        new_config = {'duration': 3.0}
        if job.Configure(new_config):
            print("Configuration updated")

        # Run power cycle
        print("Running power cycle...")
        if job.Run():
            print("Power cycle completed")
        else:
            print("Power cycle failed")

        # Stop operation
        job.Stop()
    else:
        print("Initialization failed")

if __name__ == "__main__":
    test_power_switch()
