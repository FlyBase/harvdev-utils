"""Module:: today.

Synopsis:
    A module that returns a human-readable datestamp in YYYY:MM:DD format.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu
"""

import datetime


def today():
    """Return current day in simple human-readable format: YYYY:MM:DD.

    Args:
        None.

    Returns:
        str: Date in YYYY:MM:DD format.

    """
    today = datetime.datetime.today().strftime('%y%m%d')

    return today
