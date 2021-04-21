"""Module:: sgml_to_plain_text.

Synopsis:
    A module to convert Greek unicode to plain text Greek words.

Author(s):
    Christopher Tabone ctabone@morgan.harvard.edu

"""

import re


def unicode_to_plain_text(input_string):
    r"""Convert Greek unicode to plain text Greek words.

    e.g. "\\u03B1" -> "alpha"

    Args:
        arg1 (str): The "input_string" containing Greek unicode characters to be converted.

    Returns:
        str: The same string as the input with the Greek unicode characters transliterated.

    Raises:
        KeyError: If the regex matches for a set of unicode characters but there is no exact matching plain text.

    """
    substitution_dict = {
        '\u03B1': 'alpha',
        '\u0391': 'Alpha',
        '\u03B2': 'beta',
        '\u0392': 'Beta',
        '\u03B3': 'gamma',
        '\u0393': 'Gamma',
        '\u03B4': 'delta',
        '\u0394': 'Delta',
        '\u03B5': 'epsilon',
        '\u0395': 'Epsilon',
        '\u03B6': 'zeta',
        '\u0396': 'Zeta',
        '\u03B7': 'eta',
        '\u0397': 'Eta',
        '\u03B8': 'theta',
        '\u0398': 'Theta',
        '\u03B9': 'iota',
        '\u0399': 'Iota',
        '\u03BA': 'kappa',
        '\u039A': 'Kappa',
        '\u03BB': 'lambda',
        '\u039B': 'Lambda',
        '\u03BC': 'mu',
        '\u039C': 'Mu',
        '\u03BD': 'nu',
        '\u039D': 'Nu',
        '\u03BE': 'xi',
        '\u039E': 'Xi',
        '\u03BF': 'omicron',
        '\u039F': 'Omicron',
        '\u03C0': 'pi',
        '\u03A0': 'Pi',
        '\u03C1': 'rho',
        '\u03A1': 'Rho',
        '\u03C3': 'sigma',
        '\u03A3': 'Sigma',
        '\u03C4': 'tau',
        '\u03A4': 'Tau',
        '\u03C5': 'upsilon',
        '\u03A5': 'Upsilon',
        '\u03C6': 'phi',
        '\u03A6': 'Phi',
        '\u03C7': 'chi',
        '\u03A7': 'Chi',
        '\u03C8': 'psi',
        '\u03A8': 'Psi',
        '\u03C9': 'omega',
        '\u03A9': 'Omega'
    }

    substitution = None

    try:
        substitution = re.sub(r'(\\u03[ABC9][0-9ABCDEF])', lambda m: substitution_dict[m.group()], input_string)
    except KeyError as e:
        print('Regex matched the sgml pattern &\\w+; but no key was found in the substitution dictionary.')
        print('Please check for typos in your sgml: {}'.format(e))
        raise(e)

    return substitution
