"""Module:: sub_sup_sgml_to_plain_text.

Synopsis:
    A module to convert FlyBase sub/superscript SGML to plain text square brackets.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import re


def sub_sup_sgml_to_plain_text(input_string: str) -> str:
    """Convert FlyBase superscript/subscript SGML to plain text square brackets.

    e.g. "<up>" > "["

    Args:
        arg1 (input_string): (str) The "input_string" containing characters to be converted.

    Returns:
        str: The same string as the input with the SGML characters converted.

    Raises:
        KeyError: If the regex matches for a set of SGML characters but there is no exact matching SGML.

    """
    substitution_dict = {
        '<up>': '[',
        '</up>': ']',
        '<down>': '[[',
        '</down>': ']]'
    }

    substitution = None

    try:
        substitution = re.sub(r'(<(/|)\w+>)', lambda m: substitution_dict[m.group()], input_string)
    except KeyError as e:
        print('Regex matched the sgml pattern &\\w+; but no key was found in the substitution dictionary.')
        print('Please check for typos in your sgml: {}'.format(e))
        raise(e)

    return substitution
