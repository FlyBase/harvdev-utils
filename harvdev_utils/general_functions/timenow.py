"""Module:: timenow.

Synopsis:
    A module that returns the current time as a human-readable timestamp in HH:MM:SS format.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu
"""

import datetime


def timenow():
    """Return the current time as a human-readable timestamp in HH:MM:SS format.

    Args:
        None.

    Returns:
        Time in HH:MM:SS format.

    Warnings:
        None.

    Raises:
        None.
    """
    timenow = datetime.datetime.now().strftime('%H:%M:%S')

    return timenow
