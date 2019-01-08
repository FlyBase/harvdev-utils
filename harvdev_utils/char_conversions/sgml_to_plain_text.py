"""
.. module:: sgml_to_plain_text
   :synopsis: A module to convert FlyBase SGML to plain text greek words. 

.. moduleauthor:: Christopher Tabone ctabone@morgan.harvard.edu


"""

import re

def sgml_to_plain_text(input_string):
    """A function to convert FlyBase SGML to plain text greek words. 
    e.g. &agr; -> alpha

    Args:
        input_string (str): The string containing characters to be converted.

    Returns:
        str: The same string as the input with the greek characters converted.

    Raises:
        KeyError: If the regex matches for a set of SGML characters but there is no exact matching SGML.

    """

    substitution_dict = {
    '&agr;' : 'alpha',
    '&Agr;' : 'Alpha',
    '&bgr;' : 'beta',
    '&Bgr;' : 'Beta',
    '&ggr;' : 'gamma',
    '&Ggr;' : 'Gamma',
    '&dgr;' : 'delta',
    '&Dgr;' : 'Delta',
    '&egr;' : 'epsilon',
    '&Egr;' : 'Epsilon',
    '&zgr;' : 'zeta',
    '&Zgr;' : 'Zeta',
    '&eegr;' : 'eta',
    '&EEgr;' : 'Eta',
    '&thgr;' : 'theta',
    '&THgr;' : 'Theta',
    '&igr;' : 'iota',
    '&Igr;' : 'Iota',
    '&kgr;' : 'kappa',
    '&Kgr;' : 'Kappa',
    '&lgr;' : 'lambda',
    '&Lgr;' : 'Lambda',
    '&mgr;' : 'mu',
    '&Mgr;' : 'Mu',
    '&ngr;' : 'nu',
    '&Ngr;' : 'Nu',
    '&xgr;' : 'xi',
    '&Xgr;' : 'Xi',
    '&ogr;' : 'omicron',
    '&Ogr;' : 'Omicron',
    '&pgr;' : 'pi',
    '&Pgr;' : 'Pi',
    '&rgr;' : 'rho',
    '&Rgr;' : 'Rho',
    '&sgr;' : 'sigma',
    '&Sgr;' : 'Sigma',
    '&tgr;' : 'tau',
    '&Tgr;' : 'Tau',
    '&ugr;' : 'upsilon',
    '&Ugr;' : 'Upsilon',
    '&phgr;' : 'phi',
    '&PHgr;' : 'Phi',
    '&khgr;' : 'chi',
    '&KHgr;' : 'Chi',
    '&psgr;' : 'psi',
    '&PSgr;' : 'Psi',
    '&ohgr;' : 'omega',
    '&OHgr;' : 'Omega'
    }

    substitution = None

    try:
        substitution = re.sub(r'(&\w+;)', lambda m: substitution_dict[m.group()], input_string)
    except KeyError as e:
        print('Regex matched the sgml pattern &\\w+; but no key was found in the substitution dictionary.')
        print('Please check for typos in your sgml: {}'.format(e))
        raise(e)

    return substitution