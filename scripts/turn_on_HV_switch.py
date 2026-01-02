#!/usr/bin/env python3
import logging
import sys
from optparse import OptionParser
from JobModule.device_VITREK_switch_control import Vitrek964i
import asyncio

async def only_turn_on_channel(vitrekINST, iCHANNEL:int):
    if iCHANNEL < 1 or iCHANNEL > 32: raise IOError(f'[InvalidChannel] channel {iCHANNEL} is invalid')
   #await vitrekINST.set_bank_state(0, "#h00") ## reset all relay at bank0
   #await vitrekINST.set_bank_state(1, "#h00") ## reset all relay at bank1
   #await vitrekINST.set_bank_state(2, "#h00") ## reset all relay at bank2
    await vitrekINST.reset() ## reset all relay
    await vitrekINST.set_relay_state(iCHANNEL, "ON")

mmtsPOSmap = {
        '0': 0, # resetallchannel
        '1L': 1, '1C': 2, '1R': 3,
        '2L': 4, '2C': 5, '2R': 6,
        }
def MMTSposition_to_HVchannel(mmtsPOSITION:str):
    if mmtsPOSITION in mmtsPOSmap.keys():
        return mmtsPOSmap[mmtsPOSITION]
    return 0 ## if invalid option. Regard it as disable everything
    
#def Option_Parser(argv):
#
#    usage='usage: %prog [options] arg\n'
#    parser = OptionParser(usage=usage)
#
#    parser.add_option('-p', '--position',
#            type='str', dest='position', default=None,
#            help=f'MMTS position. available options is {mmtsPOSmap.keys}. Once option received invalid entry, reset all channel'
#            )
#    parser.add_option('-d', '--delay',
#            type='float', dest='delay', default=0.05,
#            help='delay timer after turn on switch'
#            )
#    parser.add_option('-a', '--address',
#            type='str', dest='address', default=None,
#            help='RS232 device address in system. Input like "ASRL/dev/ttyUSB0::INSTR". If address set, use this address. Or use address in config file'
#            )
#    parser.add_option('-c', '--config',
#            type='str', dest='config', default='data/mmts_configurations.yaml',
#            help='Read RS232 device address like "ASRL/dev/ttyUSB0::INSTR" from yaml file. This option will be ignored if --address set'
#            )
#        
#
#
#    (options, args) = parser.parse_args(argv)
#    return options
def Option_Parser(argv):
    usage = 'usage: %prog [options] arg\n'
    parser = OptionParser(usage=usage)

    pos_choices = sorted(mmtsPOSmap.keys())

    parser.add_option(
        '-p', '--position',
        type='choice', choices=pos_choices,
        dest='position', default=None,
        help=f"MMTS position. Choices: {', '.join(pos_choices)}, 0 for reset all channel"
    )

    parser.add_option(
        '-d', '--delay',
        type='float', dest='delay', default=0.05,
        help='delay timer after turn on switch'
    )
    parser.add_option(
        '-a', '--address',
        type='str', dest='address', default=None,
        help='RS232 device address in system. Input like "ASRL/dev/ttyUSB0::INSTR". '
             'If address set, use this address. Or use address in config file'
    )
    parser.add_option(
        '-c', '--config',
        type='str', dest='config', default='data/mmts_configurations.yaml',
        help='Read RS232 device address like "ASRL/dev/ttyUSB0::INSTR" from yaml file. '
             'This option will be ignored if --address set'
    )

    (options, args) = parser.parse_args(argv)
    return options




def address_from_yaml(yamlFILE):
    '''
### used for run.IVscan.sh
RS232:
  switch_vitek: 'ASRL/dev/DAQrs232_HVswitch::INSTR'
  HV_keithley: 'ASRL/dev/DAQrs232_keithley::INSTR'
    '''
    import yaml
    with open(yamlFILE, 'r') as fIN:
        conf = yaml.safe_load(fIN)
        return conf['RS232']['switch_vitek']

def main():
    options = Option_Parser(sys.argv[1:])

    """Comprehensive example usage of the Vitrek964i class with all methods"""
    # Create controller instance
    log.debug(f'[options] {options}')


    addr = options.address if options.address else address_from_yaml(options.config)
    vitrek_device = Vitrek964i(addr)
    try:
        async def async_main(vitrek):
            # Connect to the device
            if await vitrek.connect():
                log.debug("\n===== BASIC DEVICE INFORMATION =====")
                # Get device identity
                identity = await vitrek.get_identity()
                log.debug(f"Device identity: {identity}")

                # Reset device
                await vitrek.reset()
                log.debug("Device reset completed")

                # Check if connected
                connected = vitrek.is_connected()
                log.debug(f"Connected status: {connected}")

                ### print("\n===== ERROR STATUS CHECK =====")
                ### # Check for any errors
                ### error_status = await vitrek.get_error_status()
                ### print(f"Initial error status: {error_status}")
                channel = MMTSposition_to_HVchannel(options.position)
                if channel == 0:
                    vitrek.reset()
                else:
                    log.info(f'[SetCH] channel {channel} ON')
                    await only_turn_on_channel(vitrek, channel)
                    if options.delay > 0:
                        await asyncio.sleep(options.delay)
        asyncio.run(async_main(vitrek_device))

    except Exception as e:
        log.error(f"Error during operation: {e}")
    finally:
        # Always disconnect properly
        #vitrek_device.disconnect()
        #print("Test sequence completed")
        pass ### not to reset device

log = logging.getLogger(__name__)
if __name__ == '__main__':
    import os
    loglevel = os.environ.get('LOG_LEVEL', 'INFO') # DEBUG, INFO, WARNING
    DEBUG_MODE = True if loglevel == 'DEBUG' else False
    logLEVEL = getattr(logging, loglevel)
    logging.basicConfig(stream=sys.stdout,level=logLEVEL,
                        format=f'%(levelname)-7s%(filename)s#%(lineno)s %(funcName)s() >>> %(message)s',
                        datefmt='%H:%M:%S')
    main()


