import asyncio
import argparse
from pathlib import Path
import json
from datetime import datetime

# Import the integrated controller
from integrated_controller_VITREK_KEITHLEY.py import IntegratedTestController

"""
Script Description

# Example commands:
    python sample_test_script.py config test_config.json --start-bank 0 --end-bank 1 --relays 4 --prefix SN --start-id 101 --start-v 0 --stop-v 0.8 --points 21
    python sample_test_script.py run test_config.json --vitrek "ASRL/dev/ttyUSB0::INSTR" --keithley "GPIB0::24::INSTR"

# File Naming Convention:
    20250318_123045_bank0_relay3_module_SN103_iv_scan.csv

# Safety Considerations
The implementation includes several safety features:
    - Ensuring outputs are off before switching channels
    - Opening all relays before selecting a new channel
    - Proper error handling with cleanup in failure cases
    - Systematic disconnection from devices when done
"""

async def run_from_config(config_file, vitrek_resource, keithley_resource):
    """
    Run tests based on a configuration file

    Args:
        config_file: Path to the configuration file
        vitrek_resource: VISA resource name for Vitrek 964i
        keithley_resource: VISA resource name for Keithley SourceMeter
    """
    print(f"Running tests from configuration file: {config_file}")

    # Create controller
    controller = IntegratedTestController(
        switch_resource=vitrek_resource,
        keithley_resource=keithley_resource
    )

    try:
        # Connect to devices
        connected = await controller.connect_all()
        if not connected:
            print("Failed to connect to devices, aborting test")
            return False

        # Run batch IV scan from configuration
        results = await controller.run_batch_iv_scan(config_file=config_file)

        # Report results
        if results:
            print("\nTest Results Summary:")
            print(f"Total channels tested: {len(results)}")
            print("Channels and result files:")
            for (bank, relay), filename in results.items():
                print(f"  Bank {bank}, Relay {relay}: {Path(filename).name}")

            return True
        else:
            print("No test results were obtained")
            return False

    except Exception as e:
        print(f"Error during test execution: {e}")
        return False
    finally:
        # Always disconnect properly
        await controller.disconnect_all()

async def create_test_config(output_file, start_bank, end_bank, relays_per_bank,
                           module_prefix, start_module_id, start_v, stop_v, points):
    """
    Create a test configuration file

    Args:
        output_file: Path to save the configuration file
        start_bank: First bank to include
        end_bank: Last bank to include (inclusive)
        relays_per_bank: Number of relays to use in each bank
        module_prefix: Prefix for module IDs
        start_module_id: Starting ID number
        start_v: Starting voltage for IV scans
        stop_v: Ending voltage for IV scans
        points: Number of points in each IV scan
    """
    # Create a controller (we only need it for the config creation method)
    controller = IntegratedTestController(
        switch_resource="DUMMY",  # Not connecting, so resource name doesn't matter
        keithley_resource="DUMMY"
    )

    # Generate bank/relay pairs
    bank_relay_pairs = []
    for bank in range(start_bank, end_bank + 1):
        for relay in range(1, relays_per_bank + 1):
            bank_relay_pairs.append((bank, relay))

    # Generate module mapping
    module_mapping = {}
    for i, (bank, relay) in enumerate(bank_relay_pairs):
        module_mapping[(bank, relay)] = f"{module_prefix}{start_module_id + i}"

    # Create the configuration file
    result = await controller.create_config_file(
        filename=output_file,
        bank_relay_pairs=bank_relay_pairs,
        module_mapping=module_mapping,
        start_v=start_v,
        stop_v=stop_v,
        points=points
    )

    if result:
        print(f"Configuration file created successfully: {output_file}")

        # Show the configuration content
        with open(output_file, 'r') as f:
            config = json.load(f)

        print(f"\nConfiguration Summary:")
        print(f"Voltage range: {config['start_v']}V to {config['stop_v']}V")
        print(f"Number of points: {config['points']}")
        print(f"Total channels: {len(config['channels'])}")
        print("First 3 channels:")
        for i, channel in enumerate(config['channels'][:3]):
            print(f"  Bank {channel['bank']}, Relay {channel['relay']}, Module ID: {channel['module_id']}")
        if len(config['channels']) > 3:
            print(f"  ... plus {len(config['channels']) - 3} more channels")
    else:
        print("Failed to create configuration file")

def main():
    parser = argparse.ArgumentParser(description='Silicon Module IV Testing')

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Parser for the 'run' command
    run_parser = subparsers.add_parser('run', help='Run tests from a configuration file')
    run_parser.add_argument('config', help='Path to the configuration file')

                           help='VISA resource name for Vitrek 964i')

                           help='VISA resource name for Keithley SourceMeter')

    # Parser for the 'config' command
    config_parser = subparsers.add_parser('config', help='Create a test configuration file')
    config_parser.add_argument('output', help='Path to save the configuration file')
    config_parser.add_argument('--start-bank', type=int, default=0, help='First bank to include')
    config_parser.add_argument('--end-bank', type=int, default=0, help='Last bank to include')
    config_parser.add_argument('--relays', type=int, default=8, help='Number of relays per bank')
    config_parser.add_argument('--prefix', default='SN', help='Module ID prefix')
    config_parser.add_argument('--start-id', type=int, default=1, help='Starting module ID number')
    config_parser.add_argument('--start-v', type=float, default=0.0, help='Starting voltage for IV scans')
    config_parser.add_argument('--stop-v', type=float, default=0.8, help='Ending voltage for IV scans')
    config_parser.add_argument('--points', type=int, default=21, help='Number of points in each IV scan')

    args = parser.parse_args()

    if args.command == 'run':
        asyncio.run(run_from_config(args.config, args.vitrek, args.keithley))
    elif args.command == 'config':
        asyncio.run(create_test_config(
            args.output, args.start_bank, args.end_bank, args.relays,
            args.prefix, args.start_id, args.start_v, args.stop_v, args.points
        ))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
