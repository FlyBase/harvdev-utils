"""Module:: sub_sup_to_sgml.

Synopsis:
    A module to convert bracket characters to up and down flags.

Author(s):
    Christopher Tabone ctabone@morgan.harvard.edu

"""

import re


def sub_sup_to_sgml(input_string):
    """A function to convert bracket characters to up and down flags.

    e.g. "[hello]" -> "<up>hello</up>"

    Args:
        arg1 (str): The "input_string" containing bracket characters to be converted.

    Returns:
        str: The same string as the input with the bracket characters converted to up and down flags.

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
