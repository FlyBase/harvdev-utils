from harvdev_utils.production import Synonym
from harvdev_utils.char_conversions import sub_sup_to_sgml, sgml_to_unicode
from harvdev_utils.chado_functions import (
    get_cvterm,  DataError, CodingError,
    # get_default_organism_id,
    # synonym_name_details
)
#
# general cache
# general_cache[type][symbol] = general_object
#       "      [type][uniquename] = "
# NOTE: name is not used this is not unique so do
#       not want to risk overwritting/using wrong one.
#       Symbol should be unique for a type.
#
general_cache = {}

# feature type cache.
general_type_cache = {}


def general_type_lookup(session, type_name):
    """Lookup type cvterm."""
    if type_name in general_type_cache:
        return general_type_cache[type_name]

    feature_type = None
    for cv_type_name in ['SO', 'FlyBase miscellaneous CV']:
        if not feature_type:
            try:
                feature_type = get_cvterm(session, cv_type_name, type_name)
            except CodingError:
                pass
    if not feature_type:
        raise DataError("DataError: Could not find cvterm for feature type {}".format(type_name))
    general_type_cache[type_name] = feature_type
    return feature_type


def general_symbol_lookup(session, sql_object_type, syn_object_type, type_name, synonym_name, organism_id=None, cv_name='synonym type',
                          cvterm_name='symbol', check_unique=True, obsolete='f', convert=True):
    """Lookup "other" feature that has a specific type and synonym name.

    Args:
        session (sqlalchemy.orm.session.Session object): db connection  to use.

        sql_object_type (sqlalchemy object type): i.e. Grp, CellLine, Strain

        type_name (str): <can be None> cvterm name, defining the type of feature.

        synonym_name (str): symbol to look up.

        organism_id (int): <optional> chado organism_id.

        cv_name (str): <optional> cv name defaults too 'synonym type'

        cvterm_name (str): <optional> cvterm name defaults too 'symbol'

        check_uniuqe (Bool): <optional> Set to false to fetch more than one feature with that symbol.

        obsolete ('t', 'f', 'e'): <optional> is feature obsolete
                                  t = true
                                  f = false (default)
                                  e = either not fussed.

        convert (Bool): <optional> set to True
                        wether to convert chars i.e. '[' to '<up' etc

    ONLY replace cvterm_name and cv_name if you know what exactly you are doing.
    symbol lookups are kind of special and initialized here for ease of use.

    Returns:
        Feature object or list of feature object if check_unique is passed as False.

    Raises:
        NoResultFound: If no feature found matching the synonym.

        MultipleResultsFound: If more than one feature found matching the synonym.
    """
    # Default to Dros if not organism specified.
    # if not organism_id:
    #     organism, plain_name, synonym_sgml = synonym_name_details(session, synonym_name)
    #     organism_id = organism.organism_id
    # else:
    #     # convert name to sgml format for lookup
    synonym_sgml = sgml_to_unicode(sub_sup_to_sgml(synonym_name))
    if not convert:
        synonym_sgml = synonym_name

    # Check cache
    if type_name in general_cache and synonym_sgml in general_cache[type_name]:
        return general_cache[type_name][synonym_sgml]

    synonym_type = get_cvterm(session, cv_name, cvterm_name)
    check_obs = _check_obsolete(obsolete)
    filter_spec = (Synonym.type_id == synonym_type.cvterm_id,
                   Synonym.synonym_sgml == synonym_sgml,
                   sql_object_type.is_obsolete == obsolete)

    if organism_id:
        filter_spec += (sql_object_type.organism_id == organism_id,)

    if check_obs:
        filter_spec += (sql_object_type.is_obsolete == obsolete,)
    if type_name:
        feature_type = general_type_lookup(session, type_name)
        filter_spec += (sql_object_type.type_id == feature_type.cvterm_id,)

    if check_unique:
        object = session.query(sql_object_type).join(syn_object_type).join(Synonym).\
            filter(*filter_spec).one()
    else:
        object = session.query(sql_object_type).join(syn_object_type).join(Synonym).\
            filter(*filter_spec).all()

    return object


def _check_obsolete(obsolete):
    """Check if obsolete.

    check if obsolete is one of the 3 allowed values and
    return wether obsolete should be checked.
    """
    check_obs = True
    if obsolete == 'e':
        check_obs = False
    elif obsolete != 't' and obsolete != 'f':
        raise CodingError("If specifed obsolete must be 't', 'f' or 'e'")
    return check_obs
