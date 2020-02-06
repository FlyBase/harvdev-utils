"""
.. module:: json_dump
   :synopsis: Prints out an AGR JSON data structure with metadata and data.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import json
import logging
import datetime
from utils import timenow

log = logging.getLogger(__name__)


def json_dump(json_data_object, output_filename):
    """
    Function that writes out AGR JSON file.
    Libraries:
        json, logging, datetime, alliance-flybase.utils.
    Functions:
        timenow().
    Args:
        The "json_data_object" to write, and the "output_filename".
    Returns:
        None per se, just writes to file.
    Raises:
        None.
    """

    log.info('TIME: {}. Writing data to output file.'.format(timenow()))

    with open(output_filename, 'w') as outfile:
        json.dump(json_data_object, outfile, sort_keys=True, indent=2, separators=(',', ': '))
        outfile.close()

    log.info('TIME: {}. Done writing data to output file.'.format(timenow()))

    return
