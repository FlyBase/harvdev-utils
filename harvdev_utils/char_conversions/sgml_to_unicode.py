"""Module:: sgml_to_unicode.

Synopsis:
    A module to convert FlyBase SGML to Greek characters in unicode.

Author(s):
    Christopher Tabone ctabone@morgan.harvard.edu

"""

import re


def sgml_to_unicode(input_string):
    r"""Convert FlyBase SGML to Greek characters in unicode.

    e.g. "&agr;" -> "\\u03B1"

    Args:
        arg1 (str): The "input_string" containing FB SGML characters to be converted.

    Returns:
        str: The same string as the input with the SGML characters converted to unicode.

    Raises:
        KeyError: If the regex matches for a set of SGML characters but there is no exact matching SGML.

    """
    substitution_dict = {
        '&agr;': '\u03B1',
        '&Agr;': '\u0391',
        '&bgr;': '\u03B2',
        '&Bgr;': '\u0392',
        '&ggr;': '\u03B3',
        '&Ggr;': '\u0393',
        '&dgr;': '\u03B4',
        '&Dgr;': '\u0394',
        '&egr;': '\u03B5',
        '&Egr;': '\u0395',
        '&zgr;': '\u03B6',
        '&Zgr;': '\u0396',
        '&eegr;': '\u03B7',
        '&EEgr;': '\u0397',
        '&thgr;': '\u03B8',
        '&THgr;': '\u0398',
        '&igr;': '\u03B9',
        '&Igr;': '\u0399',
        '&kgr;': '\u03BA',
        '&Kgr;': '\u039A',
        '&lgr;': '\u03BB',
        '&Lgr;': '\u039B',
        '&mgr;': '\u03BC',
        '&Mgr;': '\u039C',
        '&micro;': '\u00B5',
        '&ngr;': '\u03BD',
        '&Ngr;': '\u039D',
        '&xgr;': '\u03BE',
        '&Xgr;': '\u039E',
        '&ogr;': '\u03BF',
        '&Ogr;': '\u039F',
        '&pgr;': '\u03C0',
        '&Pgr;': '\u03A0',
        '&rgr;': '\u03C1',
        '&Rgr;': '\u03A1',
        '&sgr;': '\u03C3',
        '&Sgr;': '\u03A3',
        '&tgr;': '\u03C4',
        '&Tgr;': '\u03A4',
        '&ugr;': '\u03C5',
        '&Ugr;': '\u03A5',
        '&phgr;': '\u03C6',
        '&PHgr;': '\u03A6',
        '&khgr;': '\u03C7',
        '&KHgr;': '\u03A7',
        '&psgr;': '\u03C8',
        '&PSgr;': '\u03A8',
        '&ohgr;': '\u03C9',
        '&OHgr;': '\u03A9',
        '&lt;': '<',
        '&gt;': '>',
        '&cap;': '\u2229'
    }

    substitution = None

    try:
        substitution = re.sub(r'(&\w+;)', lambda m: substitution_dict[m.group()], input_string)
    except KeyError as e:
        print('Regex matched the sgml pattern &\\w+; but no key was found in the substitution dictionary.')
        print('Please check for typos in your sgml: {}'.format(e))
        raise(e)

    return substitution
