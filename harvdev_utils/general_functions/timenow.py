"""
.. module:: timenow
   :synopsis: A human-readable timestamp in HH:MM:SS format.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import datetime


def timenow():
    """
    A function that gives current time in simple human-readable format.
    Args:
        None.
    Returns:
        Time in HH:MM:SS format.
    Raises:
        None.
    """

    timenow = datetime.datetime.now().strftime('%H:%M:%S')

    return timenow
