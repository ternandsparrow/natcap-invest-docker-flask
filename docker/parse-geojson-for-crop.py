#!/usr/bin/env python3
# transform the official NatCap sample data shapefile into a format suitable
# for our tester UI.
import copy
import functools
import json
import sys

parsed = json.loads(sys.stdin.read())

def map_reveg_feature(f):
    coords = f['geometry']['coordinates'][0] # assuming a single poly
    first = coords[:1]
    first_three = coords[:3]
    # it's not awesome but it *does* avoid hardcoding
    triangle = first_three + first
    f['geometry']['coordinates'] = triangle
    return f

def doit(accum, curr):
    crop_type = curr['properties']['crop_type']
    curr['properties'] = {}
    try:
        accum[crop_type]
        raise Exception('Programmer error: crop type %s already exists and we' \
                + ' do not deal with that situation')
    except KeyError as e:
        # success, we don't want it to be there
        pass
    result = copy.deepcopy(parsed)
    del result['name']
    result['features'] = [curr]
    reveg = copy.deepcopy(result)
    reveg['features'] = [map_reveg_feature(x) for x in reveg['features']]
    accum[crop_type] = {'farm': result, 'reveg': reveg}
    return accum

final_result = functools.reduce(doit, parsed['features'], {})
print(json.dumps(final_result, indent=2))
