#!/usr/bin/env python3

class LoadedParameterText:
    parType = 'text'
    def __init__(self, key,val):
        self.key=key
        self.val=val['value']
    def GetCurrentValue(self) -> tuple:
        return (self.key,self.val)
class LoadedParameterTextRadio:
    parType = 'radio'
    def __init__(self, key,val):
        self.key=key
        self.val=val['value']
        self.options=val['options']
    def GetCurrentValue(self) -> tuple:
        if self.val not in self.option:
            raise IOError("[InvalidValue] LoadedParameterTextRadio::GetCurrentValue() : current value {self.val} not in options {self.options}")
        return (self.key,self.val)


def ParameterLoaderFactory(yamlLOADERoutput:dict) -> list:
    d = yamlLOADERoutput.configs
    for name, conf in d.items():
        print(name, conf)

