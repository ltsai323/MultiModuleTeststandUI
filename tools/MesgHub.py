#!/usr/bin/env python3
import json
from tools.LogTool import LOG
import tools.SocketCommands as SC
LOG_LEVEL = 1
def BUG(*mesg):
    if LOG_LEVEL < 1:
        print('#DEBUG# ', mesg)

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
def recv_socket_multi_mesg(func):
    def wrap(xarg): # only receive single str
        '''
        * foramt : [>myMesg<][>myMesg2<][>muMesg3<]
        * output : a list of [myMesg,myMesg2,myMesg3]
        '''
        arg = xarg.decode('utf-8')
        recLeng = len(arg)
        recData = []
        while True:
            startIdx = arg.find('[>')
            endedIdx = arg.find('<]')
            if startIdx == -1: break
            if endedIdx == -1: break # ignore unformatted string. Ex. '[>laksjdlfk asdklf a' or 'asdlkfjasldkjf<]'
            recData.append(arg[startIdx+2:endedIdx])
            arg = arg[endedIdx+2:]
        if len(recData) == 0:
            recData.append(arg) # if nothing found, Return all message
        return func(recData)
    return wrap


### to be deleted
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
### to be deleted end


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
def MesgEncoder_JSON(sentMESG):
    return json.dumps(sentMESG)
@recv_socket_multi_mesg
def MesgDecoder_JSON(theMESGs):
    output = []
    for theMESG in theMESGs:
        try:
            output.append( json.loads(theMESG) )
        except json.decoder.JSONDecodeError as e:
            output.append( {'n': 'ERROR', 'm': theMESG} )
            ## accept error messages
    return output

''' Assume only 1 command loaded '''
import time
from datetime import datetime
from dataclasses import dataclass
@dataclass
class MesgUnit:
    name:str
    stat:int
    mesg:str
    t:str

    @property
    def timestamp(self) -> str:
        return datetime.fromtimestamp( float(self.t) ).strftime('%Y-%m-%d %H:%M:%S')
    def __str__(self) -> str:
        return f'[{self.timestamp}:{self.name}] ({self.stat}) {self.mesg}'
def MesgUnitFactory( name:str = '', stat:str = '', mesg:str = '', timestamp:str='' ) -> MesgUnit:
    statusStr = SC.get_action_from_cmd(stat)
    return MesgUnit(
            name=name,
            stat=statusStr,
            mesg=mesg,
            t   =time.time() if timestamp=='' else timestamp )

@dataclass
class CMDUnit:
    name:str
    cmd:str # for the predefined string, this should be automatically translate to int. (Also a str)
    arg:str
    t:str
    @property
    def timestamp(self) -> str:
        if hasattr(self,'t') and self.t != '':
            return datetime.fromtimestamp( float(self.t) ).strftime('%Y-%m-%d %H:%M:%S')
        return 'CMD' # no time recorded: is a CMD
    def __str__(self):
        return f'[{self.timestamp}:{self.name}] ({self.cmd}) {self.arg}'
def CMDUnitFactory( name:str = '', cmd:str = '', arg:str = '', timestamp:str='' ) -> CMDUnit:
    ''' notice that the timestamp will not be delievered. '''
    #cmdStr = SC.get_action_from_cmd(cmd)
    return CMDUnit(
            name= name,
            cmd = cmd,
            arg = arg,
            t   = timestamp ) # by default, not to record the timestamp

def delivering_dictionary_translater( theUNIT ) -> dict:
    o = {}
    if hasattr(theUNIT, 'name'): o['n'] = theUNIT.name
    if hasattr(theUNIT, 't'): o['t'] = theUNIT.t

    if hasattr(theUNIT, 'stat'): o['s'] = theUNIT.stat # MesgUnit
    if hasattr(theUNIT, 'mesg'): o['m'] = theUNIT.mesg # MesgUnit

    if hasattr(theUNIT, 'cmd' ): o['c'] = theUNIT.cmd # CMDUnit
    if hasattr(theUNIT, 'arg' ): o['a'] = theUNIT.arg # CMDUnit
    return o


def delivered_dictionary_translater( inDICT:dict ) -> dict:
    BUG('input dict in delivered_dictionary_translater() ', inDICT)
    o = {}
    if 'n' in inDICT and inDICT['n'] != '': o['name'] = inDICT['n']
    if 't' in inDICT and inDICT['t'] != '': o['timestamp'] = inDICT['t']

    if 'm' in inDICT and inDICT['m'] != '': o['mesg'] = inDICT['m'] # MesgUnit
    if 's' in inDICT and inDICT['s'] != '': o['stat'] = inDICT['s'] # MesgUnit

    if 'c' in inDICT and inDICT['c'] != '': o['cmd'] = inDICT['c'] # CMDUnit
    if 'a' in inDICT and inDICT['a'] != '': o['arg'] = inDICT['a'] # CMDUnit
    return o


def SendSingleMesg(mesgUNIT:MesgUnit):
    return MesgEncoder_JSON( delivering_dictionary_translater(mesgUNIT) )
#def SendMultipleMesg(*mesgUNITs:list):
#    return MesgEncoder_JSON( *[delivering_dictionary_translater(mUnit) for mUnit in mesgUNITs] )

def GetSingleMesg(encodedMESG:str) -> MesgUnit:
    rec_data = MesgDecoder_JSON(encodedMESG)

    if len(rec_data) == 0: return MesgUnitFactory(name='no_data', stat='unknown')
    def first_message(recDATA):
        if isinstance(recDATA, str): return recDATA
        if isinstance(recDATA, list): return recDATA[0]
        raise IOError(f'first_message(): unknown rec_data received. Type {type(rec_data)}: Content: "{recDATA}"')
    rdata = first_message(rec_data)
    if 'c' in rdata.keys(): return CMDUnitFactory(**delivered_dictionary_translater(rdata) )
    if 's' in rdata.keys(): return MesgUnitFactory(**delivered_dictionary_translater(rdata) )
    return MesgUnitFactory(name='no_data', stat='unknown')
#def GetMultipleMesg(encodedMESG:str) -> list:
#    rec_data = MesgDecoder_JSON(encodedMESG)
#    return [ MesgUnitFactory(**delivered_dictionary_translater(rdata) ) for rdata in rec_data ]

def IsCMDUnit(theUNIT) -> bool:
    return hasattr(theUNIT, 'cmd')
def IsMesgUnit(theUNIT) -> bool:
    return hasattr(theUNIT, 'stat')


if __name__ == "__main__":
    #print(MesgDecoder_JSON(MesgEncoder_JSON( {'name':'hi', 'val':3})))
    #print(MesgDecoder_JSON('[>measlkfj alskfdj laksdfj kl<]'.encode('utf-8')))
    mesgunit = MesgUnitFactory(name='hi', stat='kk', mesg='hiiii')
    print(mesgunit)
    print( SendSingleMesg(mesgunit) )
    print( GetSingleMesg( SendSingleMesg(mesgunit)).time )
