""" Stuff that is easier to unit test without all the other dependencies """
import re

def get_records(records, all_fields):
    """ builds an array of record dicts """
    result = []
    fields = all_fields[1:] # burn the 'DeletionFlag' field
    for curr in records:
        result.append(map_fields(curr, fields))
    return result


def map_fields(record, fields):
    """ creates a dict of field name => value for the supplied record """
    result = {}
    pos = 0
    for curr in fields:
        field_name = curr[0]
        value = record[pos]
        result[field_name] = value
        pos += 1
    return result


def extract_min_max(full_string):
    """
        Extracts the min and max values from a shell output string.
        Expected input: '  Min=0.073 Max=0.158 \n'
    """
    matches = re.search('.*Min=(.*) Max=(.*) ', full_string)
    return {
        'min': matches.group(1),
        'max': matches.group(2)
    }
