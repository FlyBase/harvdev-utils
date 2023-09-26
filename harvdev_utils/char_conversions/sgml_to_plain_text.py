"""Module:: sgml_to_plain_text.

Synopsis:
    A module to convert FlyBase SGML to plain text Greek words.

Author(s):
    Christopher Tabone ctabone@morgan.harvard.edu

"""

import re


def sgml_to_plain_text(input_string):
    """Convert FlyBase SGML to plain text Greek words.

    e.g. "&agr; -> alpha"

    Args:
        arg1 (str): The "input_string" containing characters to be converted.

    Returns:
        str: The same string as the input with the SGML characters converted.

    Raises:
        KeyError: If the regex matches for a set of SGML characters but there is no exact matching SGML.

    """
    substitution_dict = {
        '&agr;': 'alpha',
        '&Agr;': 'Alpha',
        '&bgr;': 'beta',
        '&Bgr;': 'Beta',
        '&ggr;': 'gamma',
        '&Ggr;': 'Gamma',
        '&dgr;': 'delta',
        '&Dgr;': 'Delta',
        '&egr;': 'epsilon',
        '&Egr;': 'Epsilon',
        '&zgr;': 'zeta',
        '&Zgr;': 'Zeta',
        '&eegr;': 'eta',
        '&EEgr;': 'Eta',
        '&thgr;': 'theta',
        '&THgr;': 'Theta',
        '&igr;': 'iota',
        '&Igr;': 'Iota',
        '&kgr;': 'kappa',
        '&Kgr;': 'Kappa',
        '&lgr;': 'lambda',
        '&Lgr;': 'Lambda',
        '&mgr;': 'mu',
        '&Mgr;': 'Mu',
        '&ngr;': 'nu',
        '&Ngr;': 'Nu',
        '&xgr;': 'xi',
        '&Xgr;': 'Xi',
        '&ogr;': 'omicron',
        '&Ogr;': 'Omicron',
        '&pgr;': 'pi',
        '&Pgr;': 'Pi',
        '&rgr;': 'rho',
        '&Rgr;': 'Rho',
        '&sgr;': 'sigma',
        '&Sgr;': 'Sigma',
        '&tgr;': 'tau',
        '&Tgr;': 'Tau',
        '&ugr;': 'upsilon',
        '&Ugr;': 'Upsilon',
        '&phgr;': 'phi',
        '&PHgr;': 'Phi',
        '&khgr;': 'chi',
        '&KHgr;': 'Chi',
        '&psgr;': 'psi',
        '&PSgr;': 'Psi',
        '&ohgr;': 'omega',
        '&OHgr;': 'Omega',
        '&cap;': 'INTERSECTION'
    }

    substitution = None

    try:
        substitution = re.sub(r'(&\w+;)', lambda m: substitution_dict[m.group()], input_string)
    except KeyError as e:
        print('Regex matched the sgml pattern &\\w+; but no key was found in the substitution dictionary.')
        print('Please check for typos in your sgml: {}'.format(e))
        raise(e)

    return substitution
