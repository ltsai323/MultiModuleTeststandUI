#!/usr/bin/env python3
import yaml
import re
import sys
RAISE_ERROR = False

inYAMLfile = sys.argv[1]
yamlKEYs = sys.argv[2]

with open(inYAMLfile, 'r') as fIN:
    conf = yaml.safe_load(fIN)

    c = conf
    ## a key path is written either "a/b/c" or "a.b.c"; both nest the same way
    for yamlKEY in re.split(r'[./]', yamlKEYs):
        if not isinstance(c, dict) or yamlKEY not in c:
            if RAISE_ERROR:
                raise KeyError(f'[InvalidKey] key "{ yamlKEY }" in "{ yamlKEYs }" not found in yaml file "{ inYAMLfile }"')
            c = None
            break
        c = c.get(yamlKEY,None)
    if c: print(c)
