#!/usr/bin/env python3
import threading
from dataclasses import dataclass
import socket
import tools.MesgHub as MesgHub
MAX_MESG_LENG = 1024
SET_TIMEOUT = 3.0 # only used for connection checking and system cmd
@dataclass
class conn_configs:
    name:str
    ip:str
    port:int

LOG_REC='log_CommandDestnationUnit'
class module_status:
    def __init__(self):
        self.updated=False
        self.stat = 'N/A'
        self.newmesg = MesgHub.MesgUnitFactory(name='N_A', stat='N_A')
        self.log_rec = open('log_CommandDestnationUnit','w')

    def __del__(self):
        self.log_rec.close()


class CommandDestnationUnit:
    def __init__(self, connNAME, connADDR, connPORT):
        self.connConfig = conn_configs(name=connNAME, ip=connADDR, port=connPORT)
        self.stat = module_status()
        self.RegButton()
        self._name_size = len(connNAME)
        self.buttons_detail = []
        self.buttons_general = [
                connNAME+'INIT', # connect to PyModule
                connNAME+'CONNECT', # pyModule connect to hw
                connNAME+'CONFIGURE', # update configuration
                connNAME+'RUN', # run total command
                connNAME+'PAUSE', # pause the command
                connNAME+'STOP', # stop the run
                connNAME+'DESTROY', # destroy the connection to pymodule and disable the pymodule connection to hw
                ]

        self.runningFlag = threading.Event()
    def NewMesg(self, newMESG:MesgHub.MesgUnit):
        if not self.stat.updated:
            self.stat.updated = True
            self.stat.stat = newMESG.stat
            self.stat.newmesg = newMESG
            self.stat.log_rec.write(str(newMESG)+'\n')
        else:
            self.stat.stat = newMESG.stat
            self.stat.newmesg += newMESG
            self.stat.log_rec.write(str(newMESG)+'\n')

    @property
    def NameSize(self): return self._name_size
    @property
    def name(self): return self.connConfig.name

    def Initialize(self):
        print('initialized!')
        self.NewMesg( MesgHub.MesgUnitFactory(name='sys', stat='INITIALIZED') )
        return # testing

        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.connect( (self.conConfig.ip,self.connConfig.port) )
    def DESTROY(self):
        print('killed!')
        return

        self.clientSocket
    def RegButton(self):
        raise NotImplementedError('Class CommandDestnationUnit is an abstract class')
    def BtnFunc(self, message):
        raise NotImplementedError('Class CommandDestnationUnit is an abstract class')

    def no_socket_connection(self):
        if hasattr( self, 'clientSocket' ): return False
        self.NewMesg( MesgUnitFactory(name=self.name, stat='ERROR', mesg='PyModule is not initialized') )
        return True

def long_job(self, newCMD:MesgHub.CMDUnit):
    process = threading.Thread(target=send_cmd_and_wait_mesg, args=(self,newCMD))
    process.start()
def short_job(self, newCMD:MesgHub.CMDUnit):
    send_cmd(self, newCMD)



def send_cmd(cmdDESTunit:CommandDestnationUnit, incomingCMD:MesgHub.CMDUnit):
    if cmdDESTunit.no_socket_connection(): return
    cmdDESTunit.runningFlag.set()
    try:
        cmdDESTunit.clientSocket.send( MesgHub.SendSingleMesg(incomingCMD) )
        cmdDESTunit.clientSocket.settimeout(SET_TIMEOUT)
        try:
            data = cmdDESTunit.clientSocket.recv(MAX_MESG_LENG)

            if not data or data == b'':
                cmdDESTunit.NewMesg( MesgUnitFactory(name=cmdDESTunit.name, stat='GetNothing', mesg=f'send_cmd() Got nothing from server') )
            rec_data = MesgHub.GetSingleMesg(data)
            cmdDESTunit.NewMesg(rec_data)
            cmdDESTunit.NewMesg( MesgHub.MesgUnitFactory(name=cmdDESTunit.name, stat='STOPPED') )
            cmdDESTunit.runningFlag.clear()
        except socket.timeout:
            cmdDESTunit.NewMesg( MesgUnitFactory(name=cmdDESTunit.name, stat='Timeout', mesg=f'send_cmd() Timeout to get message from server.') )
    except Exception as e:
        cmdDESTunit.NewMesg( MesgUnitFactory(name=cmdDESTunit.name, stat='ERROR', mesg=f'send_cmd_and_wait_mesg() Error : "{e}" ') )

def send_cmd_and_wait_mesg(cmdDESTunit:CommandDestnationUnit, incomingCMD:MesgHub.CMDUnit):
    if cmdDESTunit.no_socket_connection(): return
    cmdDESTunit.runningFlag.set()
    try:
        cmdDESTunit.clientSocket.send( MesgHub.SendSingleMesg(incomingCMD) )
        while cmdDESTunit.runningFlag.is_set():
            cmdDESTunit.clientSocket.settimeout(SET_TIMEOUT)
            try:
                data = cmdDESTunit.clientSocket.recv(MAX_MESG_LENG)

                if not data or data == b'': continue
                rec_data = MesgHub.GetSingleMesg(data)
                cmdDESTunit.NewMesg(rec_data)
                if rec_data.stat == 'STOPPED':
                    cmdDESTunit.runningFlag.clear()
            except socket.timeout:
                continue # totally disable the timeout message. Such that all message comes from the running message
    except Exception as e:
        cmdDESTunit.NewMesg( MesgUnitFactory(name=cmdDESTunit.name, stat='ERROR', mesg=f'send_cmd_and_wait_mesg Error : "{e}" ') )



class TestUnit(CommandDestnationUnit):
    def RegButton(self):
        print('Regist button TT')
        self.buttons_detail = [
                'btnHexaControllerTT', # test button
                'btnHexaControllerT2', # test button2 asdf
                ]
    def BtnFunc(self, message):
        if not self.connConfig.name in message: return False

        print('this is my button ! '+self.connConfig.name)
        cmd = message[self.NameSize:]
        print(f'output name is {cmd}')

if __name__ == "__main__":
    ''' Only allowed one Unit keeping receiving information to reduce the connection resource. '''
    #if button_id == 'btnHexaControllerTT':
    blah = TestUnit('btnHexaController', '127.0.0.1', 2000)
    #blah = CommandDestnationUnit('kkkkr', '127.0.0.1', 2000)
    blah.Initialize()
