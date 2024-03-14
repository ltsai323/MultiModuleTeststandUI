#!/usr/bin/env python3
#import ruamel.yaml as yaml
import yaml
from tools.LogTool import LOG


### used functions
def get_content(configNAME:str, ignoreFILEnotFOUND:bool):
    try:
        with open(configNAME, 'r') as ifile:
            return yaml.safe_load(ifile)
    except OSError as e:
        if ignoreFILEnotFOUND: return {}
        raise OSError(e)
def deep_merge_dicts(dict1,dict2,ignoreNEWkey=False):
    ''' note this code cannot handle list '''
    ''' if a list inside, new list will replace old list. '''
    merged_dict = dict1.copy()
    for key, value in dict2.items():
        if ignoreNEWkey and key not in dict1.keys(): continue
        if key in merged_dict and isinstance(merged_dict[key], dict) and isinstance(value, dict):
            merged_dict[key] = deep_merge_dicts(merged_dict[key], value)
        else:
            merged_dict[key] = value
    return merged_dict
def test_merge_dict():
    dict1={ 'aa':1, 'bb':2, }
    dict2={ 'aa':9, 'cc':3, }
    print( deep_merge_dicts(dict1,dict2, ignoreNEWkey=False) )


def update_string_analyzer(updatedSTR:str='a/b/c:33'):
    if ':' not in updatedSTR: raise IOError(f'YamlLoader::AdditionalUpdate() : An invalid argument "{updatedSTR}"')
    sepIdx = updatedSTR.find(':')

    keys = updatedSTR[:sepIdx].split('/')
    val  = updatedSTR[sepIdx+1:]
    return (keys,val)
def pass_key_check(key,the_dict):
    if key not in the_dict:
        return False
    return True
def set_dict_value__nested(inDICT:dict = {}, updatedSTR:str='a/b/c:33', keyCONFIRMATION:bool=False) -> bool:
    keys,value = update_string_analyzer(updatedSTR)
    if value == None: raise IOError('YamlLoader : set_dict_value__nested() failed to get value from argument')

    ### Get the nested dictionary from key list like inDICT[key1][key2][key3]
    lastDICT = inDICT
    for key in keys[:-1]:
        if keyCONFIRMATION:
            if pass_key_check(key,lastDICT) == False:
                return False
        lastDICT = lastDICT[key]

    if pass_key_check(keys[-1],lastDICT) == False:
        LOG('Invalid Conf', 'YamlLoader::AdditionalUpdate()', f'additional configuration "{updatedSTR}" has an invalid key list "{keys}"')
        return False
    lastDICT[keys[-1]] = value
    LOG('Conf Updated', 'YamlLoader::AdditionalUpdate()', f'"{keys}" updated the configuration "{value}"')
    return True
class YamlLoader:
    '''
    read yaml file and set configurations.
    contrustructor reads default configurations and you can either use LoadNewFile or AdditionalUpdate updates the configuration.
    LoadNewFile : Additional yaml file loaded.
    AdditionalUpdate : input a configured string like "confM/confD:val"
    '''

    def __init__(self, defaultCONFIG:str):
        self.configs = get_content(defaultCONFIG, False)
    def LoadNewFile(self, customCONFIG:str, ignoreFILEnotFOUND:bool=True, ignoreNEWkey:bool = False):
        ''' Load New configs. ignoreNEWkey is an option for checking conifg. '''
        newconfigs = get_content(customCONFIG, ignoreFILEnotFOUND)

        self.configs = deep_merge_dicts(self.configs,newconfigs, ignoreNEWkey)

    def AdditionalUpdate(self, updatedSTR:str, keyCONFIRMATION:bool=True):
        '''
        arg1 : updateSTR like 'key:val' or 'keyMother/keyDaughter:val' means the secondary layer configuration
        arg1 : updateSTR like 'key:val|key2:val3' or 'keyMother/keyDaughter:val' means the secondary layer configuration
        '''

        return set_dict_value__nested(
                inDICT = self.configs,
                updatedSTR = updatedSTR,
                keyCONFIRMATION = keyCONFIRMATION )

def tester_YamlLoader():
    yaml_hardware = YamlLoader('config/hardware.defaults.yaml')
    yaml_hardware.LoadNewFile('config/hardware.yaml')
    yaml_connects = YamlLoader('config/connects.defaults.yaml')
    yaml_connects.LoadNewFile('config/connects.yaml')

    for arg_config in sys.argv[1:]:
        config_is_used = False
        if not config_is_used: config_is_used = yaml_hardware.AdditionalUpdate(arg_config,keyCONFIRMATION=True)
        if not config_is_used: config_is_used = yaml_connects.AdditionalUpdate(arg_config,keyCONFIRMATION=True)

def YamlGenerator(outFILE:str, recDICT:dict):
    '''
    input a dictionary and generate yaml output
    '''
    out_yaml = yaml.YAML()
    out_yaml.indent(mapping=2, sequence=4, offset=2)
    out_yaml.preserve_quotes = True

    with open(outFILE, 'w') as ofile:
        out_yaml.dump(recDICT, ofile)
    print(f'[YAML Generated - INFO] Output file "{outFILE}" generated')

def tester_YamlGernator():
    thedict = {
            'a': 33,
            'b': { 'kk':32, 'll':37 }
            }
    YamlGenerator('out.yaml', thedict)
class RunConfigs:
    def __init__(self, defaultYAMLfile):
        loaded_configs = get_content(defaultYAMLfile, False)
        for key,val in loaded_configs.items():
            setattr(self, key, val)
    def Update(self, key,val):
        if hasattr(self,key):
            self.key = val
        else:
            raise KeyError(f'RunConfigs.Update() : Invalid key "{key}"')

def EncodeConfigs(confDICT:dict) -> str:
    ''' 'key1/key2/key3:val|key1/key2/keY3:vaL' '''

    def nested_browse_dict(theDICT:dict, path:str="", results:list=[]) -> list:
        ''' [ 'key1/key2/key3:val', 'key1/key2/keY3:vaL' ] '''
        for key,val in theDICT.items():
            new_path = f'{path}/{key}' if path else key

            if isinstance(val,dict):
                nested_browse_dict(val, new_path, results)
            else:
                results.append(f'{new_path}:{val}')
        return results
    return '|'.join( nested_browse_dict(confDICT) )

def interpret_type(value:str):
    try:
        # Try converting to float
        float_value = float(value)
        # If conversion to float is successful, check if it's an integer
        if float_value.is_integer():
            int_value = int(float_value)
            # If it's an integer, check if it's a bool (0 or 1)
            if int_value in {0, 1}:
                return bool(int_value)
            else:
                return int_value
        else:
            return float_value
    except ValueError:
        # Conversion failed, return the original string
        return value

def DecodeConfigs(theSTR) -> dict:
    out = {}
    for setupSTR in theSTR.split('|'):
        keys = setupSTR.split(':')[0]
        val  = setupSTR.split(':')[1]
        temp_dict = out

        key_list = keys.split('/')

        for key in key_list[:-1]:
            temp_dict = temp_dict.setdefault(key, {})
        temp_dict[key_list[-1]] = interpret_type(val)
    return out

if __name__ == "__main__":
    #tester_YamlGernator()
    #tester_YamlLoader_()
    #test_merge_dict()
    a = {
            'layer1': { 'layer2': 3, 'layeR2': 5 },
            'layeR1': 3,
            }
    b = EncodeConfigs(a)
    print( b )
    print( DecodeConfigs(b) )

