"""
.. module:: generic_FB_tsv_dict
   :synopsis: Function that builds a generic FB dictionary with data and metadata elements.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import datetime


def generic_FB_tsv_dict(report_label, database):
    """Builds a generic dictionary for tsv export.
       Required libraries: datetime.
       Required functions: now().
       Required global variables: the_time, database_release, report_title.
       Input: none.
       Output: generic Alliance JSON data structure (dictionary)."""
    to_export_as_tsv = {}
    to_export_as_tsv['metaData'] = {}
    to_export_as_tsv['metaData']['title'] = report_label
    to_export_as_tsv['metaData']['dateProduced'] = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    to_export_as_tsv['metaData']['database'] = database
    to_export_as_tsv['data'] = []

    return to_export_as_tsv