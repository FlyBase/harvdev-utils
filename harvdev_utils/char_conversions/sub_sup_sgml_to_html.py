"""
.. module:: sub_sup_sgml_to_html
   :synopsis: A module to convert FlyBase up/down flags into html sub/superscript flags.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import logging

log = logging.getLogger(__name__)


def sub_sup_sgml_to_html(input_string):
    """A function to convert FlyBase up/down flags into html sub/superscript flags.
    e.g. <up>hello</up> -> <sup>hello</sup>

    Args:
        input_string (str): The string containing FlyBase up/down flags to be converted.

    Returns:
        str: The same string as the input with the html sub/superscript flags.
    """
    sub_dict = {
        '<down>': '<sub>',
        '</down>': '</sub>',
        '<up>': '<sup>',
        '</up>': '</sup>'
    }
    substitution = input_string
    for key in sub_dict.keys():
        substitution = substitution.replace(key, sub_dict[key])

    return substitution
