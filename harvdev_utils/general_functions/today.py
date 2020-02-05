"""
.. module:: today
   :synopsis: Returns a human-readable datestamp in YYYY:MM:DD format.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import datetime


def today():
    """
    A function that gives current day in simple human-readable format.
    Args:
        None.
    Returns:
        Time in YYYY:MM:DD format.
    Raises:
        None.
    """

    today = datetime.datetime.today().strftime('%y%m%d')

    return today
