"""Module:: generic_FB_tsv_dict.

Synopsis:
   Function that builds a generic FB dictionary with data and metadata elements.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import datetime


def generic_FB_tsv_dict(report_label, database):
    """Build a generic dictionary for tsv export.

    Args:
        arg1 (str): the label to be used for output files: e.g., "allele", "protein_isoforms".
        arg2 (str): the name of the database from which info was retrieved: e.g., "fb_2019_03_reporting".

    Returns:
        dict: A generic FlyBase JSON data structure (dictionary) with metadata and an empty list under "data" key.

    """
    to_export_as_tsv = {}
    to_export_as_tsv['metaData'] = {}
    to_export_as_tsv['metaData']['title'] = report_label
    to_export_as_tsv['metaData']['dateProduced'] = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    to_export_as_tsv['metaData']['database'] = database
    to_export_as_tsv['data'] = []

    return to_export_as_tsv
