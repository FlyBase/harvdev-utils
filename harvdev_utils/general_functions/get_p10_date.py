"""Module:: get_p10_date.

Synopsis:
    Converts YYMMDD/YYYYMMDD date into PUB proforma P10 field compliant date.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu
"""

import re
import logging

log = logging.getLogger(__name__)


def get_p10_date(input_date):
    """Creates proforma-compliant YYYY.M(M).D(D) date stamp from YYMMDD/YYYYMMDD input.

    Args:
        arg1 (str): A date string in YYMMDD or YYYYMMDD format.

    Returns:
        str: PUB proforma P10 field compliant YYYY.M.D date string.

    Raises:
        Will raise an exception if the input not a six or eight digit string.

    """
    # First check the input.
    if not re.match(r'(^[0-9]{6}$|^[0-9]{8}$)', input_date):
        log.error('Input string is not a six or eight digit string: {}'.format(input_date))
    # Get the year.
    if len(input_date) == 6:
        year = '20' + input_date[0:2]
    else:
        year = input_date[0:4]
    # Get the month, replacing leading zeroes.
    month = input_date[-4:-2].replace('0', '')
    # Get the day, replacing leading zeroes.
    day = input_date[-2:].replace('0', '')
    proforma_curation_date = year + '.' + month + '.' + day

    return proforma_curation_date
