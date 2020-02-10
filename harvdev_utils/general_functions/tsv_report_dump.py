"""
.. module:: tsv_report_dump
   :synopsis: Prints out FlyBase TSV data structure with metadata and data.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import csv
import logging
from ..general_functions import timenow

log = logging.getLogger(__name__)


def check_tsv_data_object(tsv_data_object):
    """
    Function that checks structure of input tsv object for writing.
    """
    log.info('TIME: {}. Checking format of input data.'.format(timenow()))

    # Check that the "tsv_data_object" is a dict.
    if type(tsv_data_object) != dict:
        log.error('The "tsv_data_object" is not of the expected type "dict".')
        raise TypeError

    # Check that expected 'data' key exists in the "tsv_data_object".
    try:
        tsv_data_object['data']
    except KeyError:
        log.error('The "tsv_data_object" is missing the expected "data" key.')
        raise KeyError

    # Check that the 'data' key represents a list.
    if type(tsv_data_object['data']) != list:
        log.error('The "tsv_data_object["data"]" object is not of the expected type "list".')
        raise TypeError

    # Check that elements in the 'data' list are themselves dicts.
    for datum in tsv_data_object['data']:
        if type(datum) != dict:
            log.error('Elements of the tsv_data_object["data"] list are not of expected type dict.')
            raise TypeError


def tsv_report_dump(tsv_data_object, output_filename, **kwargs):
    """
    Function that writes out FlyBase TSV file.
    Libraries:
        csv, logging, datetime.
    Functions:
        timenow().
    Args:
        The "tsv_data_object" to write: see "generic_FB_tsv.py".
        The tsv object should have 'metadata' key, and a 'data' key that is list of dicts.
        The "output_filename", and the keys for data elements as kwargs.
    Returns:
        None per se, just writes to file.
    Warnings:
        If "tsv_data_object" has no 'metadata' key.
    Raises:
        If tsv_data_object is not a dict.
        If tsv_data_object has no 'data' key.
        If tsv_data['data'] is not a list.
        If the first element in the 'data' list is not a dict.
    """

    log.info('TIME: {}. Writing data to output file.'.format(timenow()))

    # Check that the input "tsv_data_object" meets expectations.
    check_tsv_data_object(tsv_data_object)

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

    # Check that metadata key exists.
    try:
        output_file.write('## {}\n'.format(tsv_data_object['metaData']['title']))
        output_file.write('## Generated: {}\n'.format(tsv_data_object['metaData']['dateProduced']))
        output_file.write('## Using datasource: {}\n'.format(tsv_data_object['metaData']['database']))
    except KeyError:
        log.warning('The "tsv_data_object" has no "metadata" key.')

    # Regardless of presence/absence of metadata, write out headers.
    csv_writer = csv.DictWriter(output_file, fieldnames=headers, delimiter='\t', extrasaction='ignore')
    output_file.write('##\n## ')
    csv_writer.writeheader()

    for data_item in tsv_data_object['data']:
        csv_writer.writerow(data_item)

    try:
        output_file.write('## Finished {} report.'.format(tsv_data_object['metaData']['title']))
    except KeyError:
        output_file.write('## Finished unnamed report.')

    log.info('TIME: {}. Done writing data to output file.'.format(timenow()))

    return
