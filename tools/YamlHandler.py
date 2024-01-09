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


def update_string_analyzer(updatedSTR:str):
    if ':' not in updatedSTR: raise IOError(f'YamlLoader::AdditionalUpdate() : An invalid argument "updatedSTR"')
    sepIdx = updatedSTR.find(':')

    keys = updatedSTR[:sepIdx].split('/')
    val  = updatedSTR[sepIdx+1:]
    return (keys,val)
def pass_key_check(key,the_dict):
    if key not in the_dict:
        LOG('Invalid Conf', 'YamlLoader::AdditionalUpdate()', f'additional configuration "{updatedSTR}" has an invalid key "{key}"')
        return False
    return True
def set_dict_value__nested(inDICT:dict = {}, keys:list = [], value = None, keyCONFIRMATION:bool=False):
    if value == None: raise IOError('YamlLoader : set_dict_value__nested() failed to get value from argument')

    nestedDICT = inDICT
    for key in keys[:-1]:
        if keyCONFIRMATION:
            if pass_key_check(key,nestedDICT) == False:
                return False
        nestedDICT = nestedDICT[key]

    if pass_key_check(keys[-1],nestedDICT) == False:
        return False
    nestedDICT[keys[-1]] = value
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
        '''
        keys,val = update_string_analyzer(updatedSTR)

        return set_dict_value__nested(
                inDICT = self.configs,
                keys = keys,
                value = val,
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
if __name__ == "__main__":
    #tester_YamlGernator()
    #tester_YamlLoader_()
    test_merge_dict()

