#!/usr/bin/env python3
import json
from tools.LogTool import LOG

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




### asdf not updated
''' json dumps
[
  { n:'name', m:'mesg', s:'status', t:'timestamp' },
  { n:'name', m:'mesg', s:'status', t:'timestamp' },
  { n:'name', m:'mesg', s:'status', t:'timestamp' },
  { n:'name', c:'cmd', },
]
'''

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

''' Assume only 1 command loaded '''
class MesgHub_SingleMesg:
    def __init__(self, name):
        self.name = name
    def SendMesg(self, mesg):
        return MesgEncoder_JSON({'name': self.name, 'mesg': mesg})
    def GetCMD(self, mesg):
        cmds = MesgDecoder_JSON(mesg)
        for cmd in cmds:
            if cmd['name'] == self.name:
                LOG('Command Received', self.name, f'Command "{cmd["cmd"]}" received at time asdf')
                return cmd['cmd']
        LOG('Invalid Name Accepted', self.name, f'Commands "{cmds}" received at time asdf')
#def HostReg(name, connADDR, connPORT):
class MesgHub_MultipleMesg:
    def __init__(self, *names):
        self.names = names
        self.pending_cmds = []
    def SendCMD(self, name, cmd):
        if name not in self.names:
            LOG('Invalid Name Received', 'MesgHub_MultipleMesg', f'Input name "{name}" does not register in the MesgHub, reject the command')
            return None
        cmd_out = MesgEncoder_JSON( {'name':name, 'cmd':cmd} )

class MesgHub:
    def __init__(self, name):
        self.name = name
    def SendMesg(self, mesg_):
        return {'name': self.name, 'mesg': mesg}
    def GetMesg(self,mesg_):
        for mesg in mesgs:
            if mesg['name'] == self.name:
                return mesg['mesg']
        return ''



if __name__ == "__main__":
    #print(MesgEncoder('PowerSupply', 'encoding message'))
    #print(MesgDecoder('[>PWS__decoding message<]'.encode('utf-8')))
    #print(MesgEncoder_JSON( name='hi', val=3 ))
    print(MesgDecoder_JSON(MesgEncoder_JSON( name='hi', val=3 )))
    print(MesgDecoder_JSON('[>measlkfj alskfdj laksdfj kl<]'.encode('utf-8')))
