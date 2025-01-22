"""Module:: dump_data_to_file.

Synopsis:
    A module that prints out data (a dict with metaData dict and data list) to file.
    This module checks basic structure of the data.
    It will print out to JSON file or to TSV file.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu, Chris Tabone ctabone@morgan.harvard.edu

"""

import csv
import json
import logging
from harvdev_utils.general_functions import timenow

log = logging.getLogger(__name__)


def check_data_object(data_object, override):
    """Check the structure of the input data dict object before writing to file.

    Args:
        data_object (dict): A dictionary that includes a "metaData" key, and a "data" key with a list type value.
        override (boolean): If True, does not raise an exception for empty "data" list.

    Returns:
        empty_data_list (boolean): True if data file is empty.

    Warnings:
        Will raise a warning if the "data_object" dict has no "metaData" key.

    Raises:
        Will raise an exception if the "data_object" is not a dict.metaData
        Will raise an exception if the "data_object" has no "data" key.
        Will raise an exception if the "data_object["data"]" object is not a list.
        Will raise an exception if the "data_object["data"]" list is empty.
        Will raise an exception if the objects in the "data_object["data"]" list are not of type dict.

    """
    log.info('TIME: {}. Checking format of input data.'.format(timenow()))

    empty_data_list = False

    # Check that the "data_object" is a dict.
    if type(data_object) is not dict:
        log.error('The "data_object" is not of the expected type "dict".')
        raise TypeError

    # Check that the "data_object" has a "metaData" key.
    try:
        data_object['metaData']
    except KeyError:
        log.warning('The "data_object" is missing the expected "metaData" key.')

    # Check that the "data_object" has a "data" key.
    try:
        data_object['data']
    except KeyError:
        log.error('The "data_object" is missing the expected "data" key.')
        raise KeyError

    # Check that the "data_object["data"]" value is a list.
    if type(data_object['data']) is not list:
        log.error('The "data_object["data"]" object is not of the expected type "list".')
        raise TypeError

    # Check that the "data_object["data"]" list is not empty.
    if len(data_object['data']) == 0 and override is False:
        log.error('The "data_object["data"]" list is empty.')
        raise ValueError
    elif len(data_object['data']) == 0 and override is True:
        log.warning('The "data_object["data"]" list is empty.')
        empty_data_list = True

    # Check that the "data_object["data"]" list elements are themselves dicts.
    for datum in data_object['data']:
        if type(datum) is not dict:
            log.error('Elements of the data_object["data"] list are not of expected type dict.')
            raise TypeError

    return empty_data_list


def json_dump(json_data_object, output_filename):
    """Write "tsv_data_object" dict to JSON file.

    Args:
        arg1 (dict): A data dict. It should have metaData and data keys.
        arg2 (str): The name to use for the output file.

    Returns:
        None. It just writes out the dict to a JSON file.

    """
    log.info('TIME: {}. Writing data to output JSON file.'.format(timenow()))
    check_data_object(json_data_object, False)
    with open(output_filename, 'w') as outfile:
        json.dump(json_data_object, outfile, sort_keys=True, indent=2, separators=(',', ': '))
        outfile.close()
    log.info('TIME: {}. Done writing data to output file.'.format(timenow()))
    return


def tsv_report_dump(tsv_data_object, output_filename, print_footer=True, **kwargs):
    """Write "tsv_data_object" dict to TSV file.

    Args:
        arg1 (tsv_data_object): (dict) A data dict. It should have metaData and data keys.
        arg2 (output_filename): (str) The name to use for the output file.
        arg3 (print_footer): (bool) Whether to print out footer or not (default is true).

    Kwargs:
        headers (list): An optional list of headers.
        override (boolean): If True, no error returned for empty data.

    Returns:
        None. It just writes out the dict to a TSV file.

    Raises:
        Raises an exception if no "headers" list is supplied AND first element of "data" list has no keys itself.

    """
    log.info('TIME: {}. Writing data to output TSV file.'.format(timenow()))
    try:
        override = kwargs['override']
    except KeyError:
        override = False
    empty_data_file = check_data_object(tsv_data_object, override)
    # Can supply a list of headers under the keyword 'headers'.
    if 'headers' in kwargs.keys():
        headers = kwargs['headers']
    # Otherwise, it just takes the dictionary keys from the first data object.
    else:
        try:
            headers = tsv_data_object['data'][0].keys()
        except AttributeError:
            log.error('The first element of the tsv_data_object["data"] has no dict keys.')
            raise AttributeError

    # Open up the output file if we get this far.
    output_file = open(output_filename, 'w')

    # Check that metaData key exists.
    try:
        output_file.write('## {}\n'.format(tsv_data_object['metaData']['title']))
        output_file.write('## Generated: {}\n'.format(tsv_data_object['metaData']['dateProduced']))
        output_file.write('## Using datasource: {}\n'.format(tsv_data_object['metaData']['database']))
        try:
            note = tsv_data_object['metaData']['note']
            if type(note) is list:
                for note_part in note:
                    output_file.write('## Note: {}\n'.format(note_part))
            else:
                output_file.write('## Note: {}\n'.format(note))
        except KeyError:
            pass
        output_file.write('##\n')
    except KeyError:
        log.debug('The "tsv_data_object" has no "metaData" key.')

    # Regardless of presence/absence of metaData, write out headers.
    output_file.write('#')
    csv_writer = csv.DictWriter(output_file, fieldnames=headers, delimiter='\t', extrasaction='ignore', lineterminator='\n')
    csv_writer.writeheader()

    if empty_data_file is True:
        output_file.write('## NO DATA TO REPORT.\n')
    else:
        for data_item in tsv_data_object['data']:
            csv_writer.writerow(data_item)

    if print_footer:
        try:
            output_file.write('## Finished {}.\n'.format(tsv_data_object['metaData']['title']))
        except KeyError:
            output_file.write('## Finished report.\n')

    log.info('TIME: {}. Done writing data to output file.'.format(timenow()))

    return
