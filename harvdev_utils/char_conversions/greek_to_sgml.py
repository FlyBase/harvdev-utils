"""Module:: greek_to_sgml.

Synopsis:
    A module to convert Greek characters to FlyBase SGML for writing proformae.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu, Chris Tabone ctabone@morgan.harvard.edu

"""

import re


def greek_to_sgml(input_string):
    r"""A function to convert Greek characters into FlyBase SGML for writing proformae.

    e.g. "\\u03B1" -> "&agr;".

    Args:
        arg1 (str): "input_string" containing characters to be converted.

    Returns:
        str: The same string as the input with the Greek characters converted.

    Raises:
        KeyError: If the regex matches for a set of Greek characters but there is no exact matching Greek.
    """
    substitution_dict = {
        '\u03B1': '&agr;',
        '\u0391': '&Agr;',
        '\u03B2': '&bgr;',
        '\u0392': '&Bgr;',
        '\u03B3': '&ggr;',
        '\u0393': '&Ggr;',
        '\u03B4': '&dgr;',
        '\u0394': '&Dgr;',
        '\u03B5': '&egr;',
        '\u0395': '&Egr;',
        '\u03B6': '&zgr;',
        '\u0396': '&Zgr;',
        '\u03B7': '&eegr;',
        '\u0397': '&EEgr;',
        '\u03B8': '&thgr;',
        '\u0398': '&THgr;',
        '\u03B9': '&igr;',
        '\u0399': '&Igr;',
        '\u03BA': '&kgr;',
        '\u039A': '&Kgr;',
        '\u03BB': '&lgr;',
        '\u039B': '&Lgr;',
        '\u03BC': '&mgr;',
        '\u039C': '&Mgr;',
        '\u03BD': '&ngr;',
        '\u039D': '&Ngr;',
        '\u03BE': '&xgr;',
        '\u039E': '&Xgr;',
        '\u03BF': '&ogr;',
        '\u039F': '&Ogr;',
        '\u03C0': '&pgr;',
        '\u03A0': '&Pgr;',
        '\u03C1': '&rgr;',
        '\u03A1': '&Rgr;',
        '\u03C3': '&sgr;',
        '\u03A3': '&Sgr;',
        '\u03C4': '&tgr;',
        '\u03A4': '&Tgr;',
        '\u03C5': '&ugr;',
        '\u03A5': '&Ugr;',
        '\u03C6': '&phgr;',
        '\u03A6': '&PHgr;',
        '\u03C7': '&khgr;',
        '\u03A7': '&KHgr;',
        '\u03C8': '&psgr;',
        '\u03A8': '&PSgr;',
        '\u03C9': '&ohgr;',
        '\u03A9': '&OHgr;'
    }

    substitution = None

    try:
        substitution = re.sub(r'([\u03B1-\u03C9]|[\u0391-\u03F4])', lambda m: substitution_dict[m.group()], input_string)
    except KeyError as e:
        print('Regex matched the sgml pattern &\\w+; but no key was found in the substitution dictionary.')
        print('Please check for typos in your sgml: {}'.format(e))
        raise(e)

    return substitution
