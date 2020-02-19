"""Module:: read_csv_tsv_file.

Synopsis:
    A module that reads a csv or tsv file, extracting data and headers, as well as filename info (datestamp, extension).

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import csv
import logging
import re
from harvdev_utils.general_functions import (
    timenow
)

log = logging.getLogger(__name__)


def extract_date_from_filename(filename):
    """Extract YYMMDD/YYYYMMDD date from input string (usually a filename).

    Args:
        arg1 (str): The string to check for YYMMDD/YYYYMMDD date stamps (between periods or underscores).

    Returns:
        str: The YYMMDD/YYYYMMDD date stamp, or 'date_undetermined' if no matches found.

    Warnings:
        Raises a warning if one date stamp isn't found.

    """
    log.info('TIME: {}. Checking input file name for date stamp.'.format(timenow()))
    date_regex = r'(?<=(\.|_))([0-9]{6}|[0-9]{8})(?=(\.|_))'
    try:
        file_date = re.search(date_regex, filename).group(0)
    except AttributeError:
        log.warning('Could not find datestamp in filename: "{}"'.format(filename))
        file_date = 'date_undetermined'

    return file_date


def check_tsv_filename(filename):
    """Check filename for ".csv" or ".tsv" extension. Generate a warning if not.

    Args:
        arg1 (str): input string ("filename") to check for extension.

    Returns:
        None.

    """
    extensions = ('.tsv', '.csv')
    if filename.endswith(extensions):
        log.info('Filename "{}" has the expected ".csv/.tsv" extension.'.format(filename))
    else:
        log.warning('Filename "{}" has no ".csv/.tsv" extension.'.format(filename))

    return


def find_headers(csv_input, delimiter):
    """Scan for a column header at the top of a file, even where there many comments.

    This function scans all lines beginning with "#" at the start of a file.
    The loop breaks when the first line not starting with "#" is found.
    Any line that starts with "#" and contains the delimiter is added to a list of candidate header rows.
    The last "#" line having delimiter in the candidate list is taken to be the header.

    Args:
        arg1 (_csv.reader): A cvs reader object derived from the input file object.
        arg2 (str): The csv/tsv delimiter.

    Returns:
        list: A list of headers; list will be generic "col0", "col1", ... values if no header row is found.

    Warnings:
        Will raise a warning if no header is found. This is true of some input files that we handle: e.g., RNAcentral.
        Will raise a warning if multiple header candidates are found.
    """
    log.info('TIME: {}. Looking for header line.'.format(timenow()))
    header_list = []
    # Scan the csv input.
    for row in csv_input:
        try:
            if row[0].startswith('#'):
                log.debug('Found this comment line with {} element(s):\n\t{}'.format(len(row), row))
                if len(row) > 1:
                    header_list.append(row)
            else:
                row_size = len(row)
                log.debug('Stopping header scan at this line having {} elements:\n\t{}'.format(row_size, row))
                break
        except IndexError:
            log.debug('Ignoring an empty line: {}'.format(row))
    # If no candidate header rows found.
    if len(header_list) == 0:
        log.warning('Could not find a potential header row. Returning generic "headers" list.')
        headers = ['col{}'.format(i) for i in range(0, row_size)]
    # If multiple header candidates found.
    elif len(header_list) > 1:
        headers = header_list[-1]
        headers[0] = headers[0].replace('#', '')    # Get rid of that first "#" char in the first column.
        log.warning('Found multiple possible header rows. Going with:\n\t{}'.format(headers))
    # If only one header candidate found.
    else:
        headers = header_list[0]
        headers[0] = headers[0].replace('#', '')    # Get rid of that first "#" char in the first column.
        log.info('Found only one potential header row:\n\t{}'.format(headers))

    return headers


def extract_data_from_tsv(input_filename, **kwargs):
    """Extract data from a csv/tsv file and return it as a list of dicts.

    Detects delimiter and header info.

    Args:
        arg1 (str): The input filename.
        **kwargs: optional "delimiter" (needed if CSV Sniffer doesn't work)

    Returns:
        list: A list of dicts where dict keys match the header row (if present), or keys are generic "col0" labels.

    Raises:
        Will raise an exception if CSV Sniffer can't detect delimiter and the kwarg delimiter is not specified.

    """
    log.info('TIME: {}. Opening input file: {}.'.format(timenow(), input_filename))

    # Check filename, open the file, and detect delimiter.
    check_tsv_filename(input_filename)
    file_input = open(input_filename, 'r')
    try:
        delimiter_detected = kwargs['delimiter']
        log.info('Will use delimiter specified : "{}"'.format(delimiter_detected))
    except KeyError:
        log.info('No delimiter specified. Will try CSV Sniffer.')
        try:
            csv_sniffer = csv.Sniffer().sniff(file_input.read(1024))
            delimiter_detected = csv_sniffer.delimiter
            log.info('CSV Sniffer detected this type of delimiter: "{}".'.format(delimiter_detected))
        except ValueError:
            log.error('No delimiter specified and CSV Sniffer could not detect delimiter either.')
            raise ValueError

    # Reset the file object iterator, open the file, scan for headers.
    file_input.seek(0)
    csv_input = csv.reader(file_input, delimiter=delimiter_detected)
    headers = find_headers(csv_input, delimiter_detected)

    # Reset the file object iterator, then process into a dict.
    # Use of csv.DictReader was avoided because it does not handle zero or multiple leading comments very well.
    file_input.seek(0)
    log.info('TIME: {}. Processing rows of input file.'.format(timenow()))
    data_input = []
    row_cnt = 1
    for row in csv_input:
        log.debug('TSV: Processing row {}:\n\t{}'.format(row_cnt, row))
        if len(row) > 0:
            if not row[0].startswith('#'):
                if len(row) == len(headers):
                    row_data = {}
                    for i in range(0, len(headers)):
                        row_data[headers[i]] = row[i]
                    data_input.append(row_data)
                else:
                    log.warning('Line {} has {} part(s) instead of {} part(s).'.format(row_cnt, len(row), len(headers)))
        row_cnt += 1

    return data_input
