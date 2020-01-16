"""
.. module:: sub_sup_to_sgml
   :synopsis: A module to convert bracket characters to up and down flags.

.. moduleauthor:: Christopher Tabone ctabone@morgan.harvard.edu
"""

import re


def sub_sup_to_sgml(input_string):
    """A function to convert bracket characters to up and down flags.
    e.g. [hello] -> <up>hello</up>

    Args:
        input_string (str): The string containing bracket characters to be converted.

    Returns:
        str: The same string as the input with the bracket characters converted.

    """

    substitution_dict = {
        '[[': '<down>',
        ']]': '</down>',
        '[': '<up>',
        ']': '</up>'
    }

    substitution = None

    # Matching [ or [[ or ] or ]]
    # The craziness is because you need to differentiate capturing [ from [[ (needs negative look aheads and negative look behinds).
    substitution = re.sub(r'((?<!\])\](?!\]))|((?<!\[)\[(?!\[))|(\[\[)|(\]\])', lambda m: substitution_dict[m.group()], input_string)

    return substitution
