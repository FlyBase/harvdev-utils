"""Feature, general routines.

.. module:: chado_functions.feature
   :synopsis: Lookup and general Feature functions.

.. moduleauthor:: Ian Longden <ilongden@morgan.harvard.edu>
"""

# harvdev utils
from harvdev_utils.production import (
    Synonym, FeatureSynonym, Feature
)
from harvdev_utils.char_conversions import sub_sup_to_sgml, sgml_to_unicode
from harvdev_utils.chado_functions import (
    get_cvterm, DataError, CodingError,
    get_default_organism_id, synonym_name_details
)

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import logging
log = logging.getLogger(__name__)

#
# feature cache
# feature_cache[type][symbol] = feature_object
#       "      [type][uniquename] = "
# NOTE: name is not used this is not unique so do
#       not want to risk overwritting/using wrong one.
#       Symbol should be unique for a type.
#
feature_cache = {}

# feature type cache.
feature_type_cache = {}


def feature_type_lookup(session, type_name):
    """Lookup feature type cvterm."""
    if type_name in feature_type_cache:
        return feature_type_cache[type_name]

    feature_type = None
    for cv_type_name in ['SO', 'FlyBase miscellaneous CV']:
        if not feature_type:
            try:
                feature_type = get_cvterm(session, cv_type_name, type_name)
            except CodingError:
                pass
    if not feature_type:
        raise DataError("DataError: Could not find cvterm for feature type {}".format(type_name))
    feature_type_cache[type_name] = feature_type
    return feature_type


def add_to_cache(feature, symbol=None):
    """Add feature to cache."""
    if feature.type.name not in feature_cache:
        feature_cache[feature.type.name] = {}
    feature_cache[feature.type.name][feature.uniquename] = feature
    if symbol:
        feature_cache[feature.type.name][symbol] = feature


def get_feature_by_uniquename(session, uniquename, type_name=None, organism_id=None, obsolete='f'):
    """Get feature by the unique name.

    Get the feature from the uniquename and aswell optionally from the organsism_id and type i.e. 'gene', 'chemical entity'

    Args:
        session (sqlalchemy.orm.session.Session object): db connection  to use.

        uniquename (str): feature uniquename.

        type_name (str) : <optional> cvterm name for the type of feature.

        organism_id (int): <optional> chado organism_id.

        obsolete ('t', 'f', 'e'): <optional> is feature obsolete
                                  t = true
                                  f = false (default)
                                  e = either not fussed.

    Returns:
        Feature object

    Raises:
        NoResultFound: Feature not found.

        MultipleResultsFound: uniquename is not unique.

       CodingError: obsolete not set to one of allowed values,
    """
    feature = None
    check_obs = _check_obsolete(obsolete)
    if not type_name and not organism_id:
        feature = _simple_uniquename_lookup(session, uniquename, obsolete=obsolete)
        if feature:
            add_to_cache(feature)
    if not feature:  # uniquename not enough or type_name and/or organism specified

        filter_spec = (Feature.uniquename == uniquename,)
        if check_obs:
            filter_spec += (Feature.is_obsolete == obsolete,)

        if organism_id:
            filter_spec += (Feature.organism_id == organism_id,)
        if type_name:
            if type_name in feature_cache and uniquename in feature_cache[type_name]:
                return feature_cache[type_name][uniquename]
            feature_type = feature_type_lookup(session, type_name)
            filter_spec += (Feature.type_id == feature_type.cvterm_id,)
        feature = session.query(Feature).filter(*filter_spec).one()
    add_to_cache(feature)
    return feature


def get_feature_and_check_uname_symbol(session, uniquename, synonym, type_name=None, organism_id=None):
    """Fetch the feature and check the symbol.

    Lookup the feature by uniquename and by symbol and make sure this is the same.

    features are unique wrt:- uniquename, organism_id and type_id
    So we need to make sure we have all 3 to be safe. (though normally just the uniquename may do)

    uniquename : FBxx0000001 type. Also be aware of things like FBgn0000014:11 which is an exon.

    .. note::
        If user supplies no type_name or organism, we can get the probable organism form the synonym
        then lookup just using unique name and report problem if more than one found.

    Args:
        session (sqlalchemy.orm.session.Session object): db connection  to use.

        uniquename (str): feature uniquename.

        synonym (str): symbol to look up.

        type_name (str) : <optional> cvterm name for the type of feature.

        organism_id (int): <optional> chado organism_id.
    Returns:
        Feature object.

    Raises:
        DataError: if feature cannot be found uniquely.
    """
    try:
        feature = get_feature_by_uniquename(session, uniquename, type_name=type_name, organism_id=organism_id)
        add_to_cache(feature)
    except NoResultFound:
        message = "Unable to find Feature with uniquename {}.".format(uniquename)
        raise DataError(message)
    except MultipleResultsFound:
        message = "Found more than feature with this 'uniquename' {}.".format(uniquename)
        raise DataError(message)

    try:
        if type_name in feature_cache and synonym in feature_cache[type_name]:
            return feature_cache[type_name][synonym]
        feat_check = feature_symbol_lookup(session, type_name, synonym)
        add_to_cache(feat_check, synonym)
    except NoResultFound:
        message = "Unable to find Feature with symbol {}.".format(synonym)
        raise DataError(message)
    except MultipleResultsFound:
        message = "Found more than feature with this symbol {}.".format(synonym)
        raise DataError(message)

    if feat_check.feature_id != feature.feature_id:
        message = "Symbol {} does not match that for {}.".format(synonym, uniquename)
        raise DataError(message)
    return feature


def feature_name_lookup(session, name, organism_id=None, type_name=None, type_id=None, obsolete='f'):
    """Get feature by its name.

    Lookup feature using the feature name.

    If no organism_id is given then it will default to Dmel

    Args:
        session (sqlalchemy.orm.session.Session object): db connection  to use.

        name (str): feature name.

        type_name (str) : <optional> cvterm name for the type of feature.

        organism_id (int): <optional> chado organism_id.

        obsolete ('t', 'f', 'e'): <optional> is feature obsolete
                                  t = true
                                  f = false (default)
                                  e = either not fussed.

    Returns:
        Feature object.

    Raises:
        DataError: if feature not found uniquely.
    """
    check_obs = _check_obsolete(obsolete)
    if type_name and type_id:
        raise CodingError("Cannot specify type_name and type_id")

    # Default to Dros if no organism specified.
    if not organism_id:
        organism_id = get_default_organism_id(session)

    feature_type = None
    if type_name:
        feature_type = feature_type_lookup(session, type_name)
        type_id = feature_type.cvterm_id

    filter_spec = (Feature.name == name,
                   Feature.organism_id == organism_id)
    if check_obs:
        filter_spec += (Feature.is_obsolete == obsolete,)
    if type_id:
        filter_spec += (Feature.type_id == type_id,)
    try:
        feature = session.query(Feature).filter(*filter_spec).one_or_none()
    except MultipleResultsFound:
        raise DataError("DataError: Found multiple with name {} for type '{}'.".format(name, feature_type.name))
    if feature:
        add_to_cache(feature)
    return feature


def feature_synonym_lookup(session, type_name, synonym_name, organism_id=None, cv_name='synonym type', cvterm_name='symbol', check_unique=False, obsolete='f'):
    """Get feature from the synonym.

    Lookup to see if the synonym has been used before. Even if not current.
    Check for uniqueness if requested.

    Args:
        session (sqlalchemy.orm.session.Session object): db connection  to use.

        type_name (str): cvterm name, defining the type of feature.

        synonym_name (str): symbol to look up.

        organism_id (int): <optional> chado organism_id.

        cv_name (str): <optional> cv name defaults too 'synonym type'

        cvterm_name (str): <optional> cvterm name defaults too 'symbol'

        obsolete ('t', 'f', 'e'): <optional> is feature obsolete
                                  t = true
                                  f = false (default)
                                  e = either not fussed.

    Returns:
        List of feature objects or Feature depending on check_unique.

    Raises:
        DataError: If cvterm for type not found.
                   If feature cannot be found uniquely.

    """
    check_obs = _check_obsolete(obsolete)

    # Default to Dros if not organism specified.
    if not organism_id:
        organism_id = get_default_organism_id(session)

    # convert name to sgml format for lookup
    synonym_sgml = sgml_to_unicode(sub_sup_to_sgml(synonym_name))

    # check cache
    if type_name in feature_cache and synonym_sgml in feature_cache[type_name]:
        return feature_cache[type_name][synonym_sgml]

    # get feature type expected from type_name
    feature_type = feature_type_lookup(session, type_name)
    synonym_type = get_cvterm(session, cv_name, cvterm_name)

    filter_spec = (Synonym.type_id == synonym_type.cvterm_id,
                   Synonym.synonym_sgml == synonym_sgml,
                   Feature.organism_id == organism_id,
                   Feature.type_id == feature_type.cvterm_id,)

    if check_obs:
        filter_spec += (Feature.is_obsolete == obsolete,)

    try:
        features = session.query(Feature).join(FeatureSynonym).join(Synonym).\
            filter(*filter_spec).all()
    except NoResultFound:
        raise DataError("DataError: Could not find current synonym '{}', sgml = '{}' for type '{}'.".format(synonym_name, synonym_sgml, cvterm_name))

    if not check_unique:
        return features

    # fs has pub so there may be many of the same symbols with different pubs
    # check this is the case.
    uniquecheck = None
    for feat in features:
        if uniquecheck and uniquecheck != feat.uniquename:
            raise DataError("DataError: Could not find UNIQUE current synonym '{}', sgml = '{}' for type '{}'.".format(synonym_name, synonym_sgml, cvterm_name))
        else:
            uniquecheck = feat.uniquename

    if uniquecheck:
        add_to_cache(feat)
        return feat

    raise DataError("DataError: Could not find current unique synonym '{}', sgml = '{}' for type '{}'.".format(synonym_name, synonym_sgml, cvterm_name))


def feature_symbol_lookup(session, type_name, synonym_name, organism_id=None, cv_name='synonym type',
                          cvterm_name='symbol', check_unique=True, obsolete='f', convert=True):
    """Lookup feature that has a specific type and synonym name.

    Args:
        session (sqlalchemy.orm.session.Session object): db connection  to use.

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
    if not organism_id:
        organism, plain_name, synonym_sgml = synonym_name_details(session, synonym_name)
        organism_id = organism.organism_id
    else:
        # convert name to sgml format for lookup
        synonym_sgml = sgml_to_unicode(sub_sup_to_sgml(synonym_name))
    if not convert:
        synonym_sgml = synonym_name
    log.warning("convert is {} value is now '{}'".format(convert, synonym_sgml))

    # Check cache
    if type_name in feature_cache and synonym_sgml in feature_cache[type_name]:
        return feature_cache[type_name][synonym_sgml]

    synonym_type = get_cvterm(session, cv_name, cvterm_name)
    check_obs = _check_obsolete(obsolete)
    filter_spec = (Synonym.type_id == synonym_type.cvterm_id,
                   Synonym.synonym_sgml == synonym_sgml,
                   Feature.organism_id == organism_id,
                   FeatureSynonym.is_current == 't')

    if check_obs:
        filter_spec += (Feature.is_obsolete == obsolete,)
    if not type_name or type_name == 'gene':
        filter_spec += (~Feature.uniquename.contains('FBog'),)
    if type_name:
        feature_type = feature_type_lookup(session, type_name)
        filter_spec += (Feature.type_id == feature_type.cvterm_id,)

    if check_unique:
        feature = session.query(Feature).join(FeatureSynonym).join(Synonym).\
            filter(*filter_spec).one()
        add_to_cache(feature, synonym_sgml)
    else:
        feature = session.query(Feature).join(FeatureSynonym).join(Synonym).\
            filter(*filter_spec).all()

    return feature


def _simple_uniquename_lookup(session, uniquename, obsolete='f'):
    """
    Lookup feature by uniquename only. Will probably work most times.

    returns feature if found uniquely or None if more than one found.

    Raises error NoResultFound if not found
    """
    check_obs = _check_obsolete(obsolete)
    filter_spec = (Feature.uniquename == uniquename,)
    if check_obs:
        filter_spec += (Feature.is_obsolete == obsolete,)
    try:
        feature = session.query(Feature).filter((*filter_spec)).one_or_none()
        return feature
    except MultipleResultsFound:
        return None


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
