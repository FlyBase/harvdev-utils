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
        str: Time in HH:MM:SS format.

    """
    timenow = datetime.datetime.now().strftime('%H:%M:%S')

    return timenow
