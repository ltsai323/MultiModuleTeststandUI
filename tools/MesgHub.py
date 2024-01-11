#!/usr/bin/env python3
import json

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
        return ('[>' + func(*args, **kwargs) + '<]').encode('utf-8')
    return wrap
def recv_socket_mesg(func):
    def wrap(xarg): # only receive single str
        arg = xarg.decode('utf-8')
        if '[>' == arg[:2] and '<]' == arg[-2:]:
            return func(arg[2:-2])
        return func(arg)
    return wrap


@send_socket_mesg
def MesgEncoder(theTYPE,theMESG):
    if '__' in theMESG:
        raise ValueError(f'input message "{theMESG}" contains "__", which is preserved word.')
    mesgType = encoded_type.get(theTYPE,theTYPE) # Search for a shorted type. If nothing found, show original type.
    return '__'.join( [mesgType,theMESG] )
@recv_socket_mesg
def MesgDecoder(theMESG):
    mesgs = theMESG.split('__')
    ## if the input message is not formatted. Directly show it up instead of block it.
    if len(mesgs) != 2: return ('undefined',theMESG)
    mesgtype, mesg = mesgs
    mesgType = decoded_type.get(mesgtype,mesgtype)
    return (mesgType, mesg)



@send_socket_mesg
def MesgEncoder_JSON(*sentMESG):
    return json.dumps(sentMESG)
@recv_socket_mesg
def MesgDecoder_JSON(theMESG):
    try:
        return json.loads(theMESG)
    except json.decoder.JSONDecodeError as e:
        return {'name': 'ERROR', 'mesg': theMESG}
        ## accept error messages


if __name__ == "__main__":
    #print(MesgEncoder('PowerSupply', 'encoding message'))
    #print(MesgDecoder('[>PWS__decoding message<]'.encode('utf-8')))
    #print(MesgEncoder_JSON( name='hi', val=3 ))
    print(MesgDecoder_JSON(MesgEncoder_JSON( name='hi', val=3 )))
    print(MesgDecoder_JSON('[>measlkfj alskfdj laksdfj kl<]'.encode('utf-8')))
