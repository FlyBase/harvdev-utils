"""Module:: count_value_frequency.

Synopsis:
    A module that counts frequency of all values in a list and prints results to log file.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import logging

log = logging.getLogger(__name__)


def count_value_frequency(input_list):
    """Print the frequency of all values in a list.

    Args:
        arg1 (list): the list of values to be assessed.

    Returns:
        None. Results are printed to log file.

    To do:
        Alternative approaches include a try/except method to increment count for a given "count_dict" key.
        Initial tests on lists of a million values find only small sub-second differences in performance.
        Re-assess if data size increases dramatically.

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
