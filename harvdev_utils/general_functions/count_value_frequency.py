"""
.. module:: count_value_frequency
   :synopsis: Logs the frequency of all values in a list.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import logging

log = logging.getLogger(__name__)


def count_value_frequency(input_list):
    """
    A function that logs frequency of values in a list.
    Args:
        A list.
    Returns:
        Logs value frequency, no return per se.
    Raises:
        None.
    """

    unique_values = set(input_list)
    count_dict = {}
    for value in unique_values:
        count_dict[value] = 0
    for element in input_list:
        count_dict[element] += 1
    for k, v in count_dict.items():
        log.info('Value: {}; count: {}'.format(k, v))

    return
