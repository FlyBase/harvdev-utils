"""Synonym, general routines.

.. module:: Synonym
   :synopsis: Lookup and general synonym functions.

.. moduleauthor:: Ian Longden <ilongden@morgan.harvard.edu>
"""
from harvdev_utils.chado_functions import CodingError
from harvdev_utils.chado_functions.organism import get_default_organism, get_organism
import re
from harvdev_utils.char_conversions import (
    sgml_to_plain_text, sub_sup_to_sgml, sgml_to_unicode
)
from sqlalchemy.orm.session import Session
from typing import Tuple


def synonym_name_details(session: Session, synonym_name: str, nosup: bool=False) -> Tuple:
    r"""Get synonym details.

        Process the synonym_name given and check for organism specific stuff
        and report back organism as well as the plain text and sgml versions.

        if synonym has '\' in it the split and use first bit as the species abbreviation
        Also check for species starting with T: as this is some special shit.

    Args:
        session (sqlalchemy.orm.session.Session object): db connection to use.

        synonym_name (str): synonym name to be processed.

    Returns:
        organism for the entry,

        plain-text version of name,

        unicode version of text with sup to sgml

    NOTE:
        So for synonym_name of 'Hsap\0005-&agr;-[001]

        organism -> Organism object for homo sapiens

        plain text -> 'Hsap\\00005-alpha-[001]'

        unicode version -> 'Hsap\\00005-α-<up>001</up>'
    """
    pattern = r"""
        ^([A-Z]:){0,1}   # May have T: or not {0 or 1} Not sure of variety so any captial letter is fine
        ([^\\\s]+)       # possible species abbreviation, Non space chars and not a '\'
        \\               # forward slash
        (.*)             # anything else
    """
    s_res = re.search(pattern, synonym_name, re.VERBOSE)

    if s_res:  # matches the pattern above
        t_bit = s_res.group(1)
        abbr = s_res.group(2)
        end_name = s_res.group(3)
        try:
            organism = get_organism(session, short=abbr)
        except CodingError:  # Not a species abbr so continue as normal
            return get_default_organism(session), sgml_to_plain_text(synonym_name), sgml_to_unicode(sub_sup_to_sgml(synonym_name))

        name = "{}{}\\{}".format(t_bit or '', abbr, end_name)
        if nosup:
            return organism, sgml_to_plain_text(name), sgml_to_unicode(name)
        else:
            return organism, sgml_to_plain_text(name), sgml_to_unicode(sub_sup_to_sgml(name))
    else:
        return get_default_organism(session), sgml_to_plain_text(synonym_name), sgml_to_unicode(sub_sup_to_sgml(synonym_name))
