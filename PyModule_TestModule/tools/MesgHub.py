#!/usr/bin/env python3

''' message format: [>INDICATOR__MESSAGE<] '''
''' ex : [>PWR__Enabled<] '''
decoded_type = {
        'ERR': 'ERROR',
        'PWS': 'PowerSupply',
        'HXC': 'HexaController',
        'CMD': 'CommandPC',
        'TST': 'TestStand',
        }
encoded_type = { val:key for key,val in decoded_type.items() }

def send_socket_mesg(func):
    def wrap(*args, **kwargs):
        return '[>' + func(*args, **kwargs) + '<]'
    return wrap
@send_socket_mesg
def MesgEncoder(theTYPE,theMESG):
    if '__' in theMESG:
        raise ValueError(f'input message "{theMESG}" contains "__", which is preserved word.')
    mesgType = encoded_type.get(theTYPE,theTYPE) # Search for a shorted type. If nothing found, show original type.
    return '__'.join( [mesgType,theMESG] )



def recv_socket_mesg(func):
    def wrap(*args, **kwargs):
        ## if the input message is not formatted. Directly show it up instead of block it.
        new_args = [ arg[2:-2] if '[>' == arg[:2] and '<]' == arg[-2:] else arg for arg in args ]
        new_kwargs = { key:arg[2:-2] if '[>' == arg[:2] and '<]' == arg[-2:] else arg for key,arg in kwargs.items() }

        return func(*new_args,**new_kwargs)
    return wrap
@recv_socket_mesg
def MesgDecoder(theMESG):
    mesgs = theMESG.split('__')
    ## if the input message is not formatted. Directly show it up instead of block it.
    if len(mesgs) != 2: return ('undefined',theMESG)
    mesgtype, mesg = mesgs
    mesgType = decoded_type.get(mesgtype,mesgtype)
    return (mesgType, mesg)

if __name__ == "__main__":
    print(MesgEncoder('PowerSupply', 'encoding message'))
    print(MesgDecoder('[>PWS__decoding message<]'))
