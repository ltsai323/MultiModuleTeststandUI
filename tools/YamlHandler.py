#!/usr/bin/env python3
import ruamel.yaml as yaml


### used functions
def get_content(configNAME:str, ignoreFILEnotFOUND:bool):
    try:
        with open(configNAME, 'r') as ifile:
            return yaml.safe_load(ifile)
    except OSError as e:
        if ignoreFILEnotFOUND: return {}
        raise OSError(e)
def deep_merge_dicts(dict1, dict2):
    merged_dict = dict1.copy()
    for key, value in dict2.items():
        if key in merged_dict and isinstance(merged_dict[key], dict) and isinstance(value, dict):
            merged_dict[key] = deep_merge_dicts(merged_dict[key], value)
        else:
            merged_dict[key] = value
    return merged_dict


class YamlLoader:
    '''
    read 2 yaml file and set configurations.
    defaultCONFIG : All available options listed on it.
    custom_CONFIG : Customized options overwrite the default options.
    '''

    def __init__(self, defaultCONFIG:str, custom_CONFIG:str):
        oldconfigs = get_content(defaultCONFIG, False)
        newconfigs = get_content(custom_CONFIG, True)
        self.configs = deep_merge_dicts(oldconfigs,newconfigs)

def tester_YamlLoader():
    a = YamlLoader('input.defaults.yaml', 'input.yaml')
    print(a.configs)

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
    tester_YamlGernator()

