"""Module:: get_db_info.

Synopsis:
    A module that gets bulk data from db to create new object, or add info to an exising object.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import logging
from harvdev_utils.psycopg_functions import (
    connect, current_features_by_uname_regex, Allele, Construct, Feature, Gene, Insertion, SeqFeat, Tool
)

log = logging.getLogger(__name__)


def get_features_by_uname_regex(db_connection, feat_regex):
    """Get all current, non-analysis features for a given uniquename regex.

    Args:
        arg1 (psycopg2.extensions.connection): A psycopg2 db connection.
        arg2 (str): The regex for a FlyBase feature type of interest: e.g., r'^FBgn[0-9]{7}$'.

    Returns:
        dict: A feature.uniquename-keyed dict of Feature-type objects (appropriate object type for FB-ID type).

    Raises:
        Raises exception if Feature-type Object to use cannot be determined from the FB-ID regex.

    """
    log.info('Getting FlyBase features having uniquename like "{}".'.format(feat_regex))
    class_dict = {
        '^FBal[0-9]{7}$': Allele,
        '^FBtp[0-9]{7}$': Construct,
        '^FBgn[0-9]{7}$': Gene,
        '^FBti[0-9]{7}$': Insertion,
        '^FBto[0-9]{7}$': Tool,
        '^FBsf[0-9]{10}$': SeqFeat
    }
    try:
        ThisFeature = class_dict[feat_regex]
        log.info('The feature.uniquename regex "{}" corresponds to this type of Feature Class: "{}".'.format(feat_regex, str(ThisFeature)))
    except TypeError:
        ThisFeature = Feature
        log.info('The feature.uniquename regex "{}" does not correspond to a specific Feature type. \
                  Using generic Feature Class: "{}".'.format(feat_regex, str(ThisFeature)))

    formatted_sql_query = current_features_by_uname_regex.format(feat_regex)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    log.info('Found {} results for this query.'.format(len(db_results)))

    feature_dict = {}
    for row in db_results:
        feat_id = row[0]
        org_abbr = row[1]
        fname = row[2]
        uname = row[3]
        ftype = row[4]
        analysis = row[5]
        obsolete = row[6]
        feature_dict[uname] = ThisFeature(feat_id, org_abbr, fname, uname, ftype, analysis, obsolete)

    log.info('Returning feature dict with {} entries.\n'.format(len(feature_dict.keys())))

    return feature_dict


def confirm_attribute(item, attribute):
    """Check that an attribute exists for some object or dict.

    Args:
        arg1 (dict or object): The object to check. May be a dict, or an object like a FB Feature.
        arg2 (str): The attribute which will be checked.

    Returns:
        None.

    Raises:
        Raises an exception if attribute to check does not exist for the object.

    """
    if type(item) == dict:
        if item.__contains__(attribute) is True:
            pass
        else:
            raise KeyError('Attribute {} does not exist.'.format(attribute))
    else:
        if hasattr(item, attribute) is True:
            pass
        else:
            raise AttributeError('Attribute {} does not exist.'.format(attribute))

    return


def get_dict_value(this_dict, this_key):
    """Get value from a dict given some key, or return None if no value to get.

    Args:
        arg1 (dict): A dictionary from which to look up a value.
        arg2 (str): The key with which to look up a dict value.

    Returns:
        object: The value for a key, it if exists. Otherwise, returns None.

    """
    try:
        this_value = this_dict[this_key]
    except KeyError:
        log.debug('Dictionary has no attribute: {}. Returning "None"'.format(this_key))
        this_value = None

    return this_value


def format_sql_query(sql_query, *arguments):
    """Format a string (sql query) given an optional list of arguments.

    Args:
        arg1 (str): An input string representing an sql query; may have "{}" placeholders for formatting.
        *args: A list of arguments to insert into the string via the .format() method.

    Returns:
        str: A formatted sql query that combines query with arguments (if needed).

    """
    if len(arguments) == 0:
        formatted_sql_query = sql_query
    else:
        formatted_sql_query = sql_query.format(*arguments)

    return formatted_sql_query


def check_unique_results(db_results):
    """Check that keys (column 1 values) in db results appear only once and are thus unique.

    Args:
        arg1 (list): A list of tuples (sql db results).

    Returns:
        None. Simply checks.

    Raises:
        Will raise an exception if any values in column 1 appear more than once.
    """
    result_count = len(db_results)
    unique_key_column_values = set([row[0] for row in db_results])
    key_count = len(unique_key_column_values)

    if result_count > key_count:
        raise ValueError('Values in the first column are not unique. Try "add_list_info" function instead.')

    return


def check_key_overlap(data_dict, db_results):
    """Check overlap of "data_dict" keys with "db_results" keys (column 1).

    Args:
        arg1 (dict): A data_dict into which db_results are to be added (after this function).
        arg2 (list): A list of tuples (db_results) that are to be added to the data_dict (later on).

    Returns:
        None.

    Warnings:
        Raises a warning if there is no overlap in keys.

    """
    data_keys = set(data_dict.keys())
    db_keys = set([row[0] for row in db_results])
    key_overlap = set(data_keys.intersection(db_keys))
    if len(key_overlap) == 0:
        log.warning('There is no overlap between the data_dict keys and the db results keys.')

    return


def get_key_value(row):
    """Determine key:value pairs for some tuple (a row in db results).

    Args:
        arg1 (tuple): A db result row.

    Returns:
        obj1: a "row_key" corresponding to column 1 of the db result row: tuple[0].
        obj2: a "row_value"; handling depends on the number of columns in the db result row.
            If only two columns in row, "row_value" = col2 value.
            If row has n > 2 columns, "row_value" = tuple of values in columns 2-n.

    Raises:
        Will raise an exception if result row has only one column, since no value to get.

    """
    if len(row) < 2:
        raise ValueError('Row of results must have at least two columns to assign key and value.')
    else:
        row_key = row[0]
        if len(row) == 2:
            row_value = row[1]
        else:
            row_value = tuple(row[1:])

    return row_key, row_value


def build_uniq_db_result_dict(db_results):
    """Convert db_results into a dict (keyed by column 1 values).

    Args:
        arg1 (list): A list of tuples (db_results). Must have unique values in column 1.

    Returns:
        dict: A dict where keys are column 1 values and results are columns 2-n values.
            Value will be a tuple if a row of db_results has n > 2 columns.

    """
    # Check there's only one row per "db_results" key (i.e, row's first value).
    check_unique_results(db_results)

    # Make a db result dict.
    db_dict = {}
    for row in db_results:
        row_key, row_value = get_key_value(row)
        db_dict[row_key] = row_value

    return db_dict


def build_list_db_result_dict(db_results):
    """Convert db_results into a dict (keyed by column 1 values). Values are lists.

    Args:
        arg1 (list): A list of tuples (db_results). Expecting many values per unique value in column 1.

    Returns:
        dict: A dict where keys are column 1 values and results are lists of values.
            Elements in the list will represent columns 2-n values of the db query.
            Each element in the list will be a tuple if a row of db_results has n > 2 columns.
            Otherwise, each element in the list will simply correspond to value in column 2.

    """
    # Make a db result dict.
    db_dict = {}
    for row in db_results:
        row_key, row_value = get_key_value(row)
        if db_dict.__contains__(row_key) is True:
            db_dict[row_key].append(row_value)
        else:
            db_dict[row_key] = [row_value]

    return db_dict


def add_unique_info(data_dict, attribute, db_connection, sql_query, *arguments):
    """Add a unique value for a given attribute to each object in some ID-keyed data_dict.

    For example, get current symbol for each Gene object.
    Contrast with "add_list_info()" function, which adds a list of values for a given attribute.

    Args:
        arg1 (dict): An FB-ID keyed dict of dicts or objects (e.g., Gene or Allele objects).
        arg2 (str): An attribute for which db info will be added to each object in the input data_dict.
        arg3 (psycopg2.extensions.connection): A psycopg2 db connection.
        arg4 (str): A string representing an sql query.
        *arg: A list of arguments to be added into sql query by the .format() method.
        The data_dict FB-ID keys will be matched up to values in column 1 of db results for info transfer.

    Returns:
        dict: The input "data_dict", but now with values from the db added to "attribute" specified for objects.
            There will be a single value for the specified attribute.
            That value can be a tuple, as determined by "get_key_value()".

    Warnings:
        Raises a warning if no overlap of data_dict keys with db_results, via "check_key_overlap()".

    Raises:
        Raises an exception if values in column 1 of db_results are not unique, via "check_unique_results()".
            In other words, the expectation is that each FB ID-keyed object has only one result in the db.
            For example, finding multiple "current symbols" for a gene would be unexpected - raise in that case.

    """
    # Perform the query.
    log.info('Adding unique db info to this attribute: {}'.format(attribute))
    formatted_sql_query = format_sql_query(sql_query, *arguments)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    log.info('Found {} results for this query.'.format(len(db_results)))

    # Check there's only one row per "db_results" key (i.e, row's first value).
    check_unique_results(db_results)

    # Check that data_dict keys overlap with values in column one of db results.
    check_key_overlap(data_dict, db_results)

    # Now add the results.
    add_cnt = 0
    for row in db_results:
        row_key, row_value = get_key_value(row)
        try:
            target = data_dict[row_key]
        except KeyError:
            log.debug('The db results key "{}" does not exist in the target data_dict.'.format(row_key))
            continue
        # Action depends on whether info is being added to a dict or some other object type.
        if type(target) == dict:
            target[attribute] = row_value
            add_cnt += 1
        else:
            setattr(target, attribute, row_value)
            add_cnt += 1

    log.info('Added {} values to the {} attribute.\n'.format(add_cnt, attribute))

    return data_dict


def add_list_info(data_dict, attribute, db_connection, sql_query, *arguments):
    """Add a list of values for a given attribute to each object in some ID-keyed data_dict.

    For example, get a list of pubs for each Gene object.
    Contrast with "add_unique_info()" function, which adds a single value for a given attribute.

    Args:
        arg1 (dict): An FB-ID keyed dict of dicts or objects (e.g., Gene or Allele objects).
        arg2 (str): An attribute for which db info will be added to each object in the input data_dict.
        arg3 (psycopg2.extensions.connection): A psycopg2 db connection.
        arg4 (str): A string representing an sql query.
        *arg: A list of arguments to be added into sql query by the .format() method.
        The data_dict FB-ID keys will be matched up to values in column 1 of db results for info transfer.

    Returns:
        dict: The input "data_dict", but now with values from the db added to "attribute" specified for objects.
            There will be a list of values for the specified attribute.
            That value can be a tuple, as determined by "get_key_value()".

    Warnings:
        Raises a warning if no overlap of data_dict keys with db_results, via "check_key_overlap()".

    """
    # Perform the query.
    log.info('Adding list of db info to this attribute: {}'.format(attribute))
    formatted_sql_query = format_sql_query(sql_query, *arguments)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    log.info('Found {} results for this query.'.format(len(db_results)))

    # Check for overlap in db_result and data_dict keys.
    check_key_overlap(data_dict, db_results)

    # Set targeted attribute to an empty list if None.
    # This indicates attribute has been evaluated; an empty list means results sought but none found.
    for key, target in data_dict.items():
        # First confirm that the attribute to update exists for the object.
        empty_list = []
        if type(target) == dict:
            target[attribute] = empty_list
            log.debug('Before adding values, attribute {} set to this: {}.'.format(attribute, empty_list))
        else:
            setattr(target, attribute, empty_list)
            log.debug('Before adding values, attribute {} set to this: {}.'.format(attribute, empty_list))

    # Build a dict of the db_results.
    db_results_dict = build_list_db_result_dict(db_results)

    # Now add the results.
    add_cnt = 0
    for key, db_value in db_results_dict.items():
        log.debug('Trying to add this: {}: {}'.format(key, db_value))
        try:
            target = data_dict[key]
        except KeyError:
            log.debug('The db results key "{}" does not exist in the target data_dict.'.format(key))
            continue
        # Action depends on whether info is being added to a dict or some other object type.
        if type(target) == dict:
            target[attribute].extend(db_value)
            add_cnt += 1
        else:
            getattr(target, attribute).extend(db_value)
            add_cnt += 1

    log.info('Added values to the {} attribute of {} objects.\n'.format(attribute, add_cnt))

    return data_dict


def add_unique_dict_info(data_dict, att_key, new_att, db_connection, sql_query, *arguments):
    """Add new value to some attribute based on value of another attribute for the same object.

    For example, given a gene's organism_id, get the corresponding organism name.

    Args:
        arg1 (dict): An FB-ID keyed dict of dicts or objects (e.g., Gene or Allele objects).
        arg2 (str): An "att_key" attribute that will be used to look up a corresponding new value.
        arg3 (str): A "new_att" attribute to which new value will be added.
        arg4 (psycopg2.extensions.connection): A psycopg2 db connection.
        arg5 (str): A string representing an sql query.
        *arg: A list of arguments to be added into sql query by the .format() method.
        The object's "att_key" will be matched up to values in column 1 of db results for info transfer.

    Returns:
        dict: The input "data_dict", but now with values from the db added to "new_att" attribute of objects.
            That value can be a tuple, as determined by "get_key_value()" in "build_uniq_db_result_dict()".

    Warnings:
        Raises a warning if no overlap of data_dict keys with db_results, via "check_key_overlap()".

    Raises:
        Raises an exception if values in column 1 of db_results are not unique.
            This happens via "check_unique_results()" in "build_uniq_db_result_dict()".
            In other words, the expectation is that each "att_key" value has only one corresponding "new_att" value.
            For example, finding multiple organism.abbrevation for a given organism_id would be unexpected.

    """
    # Perform the query.
    log.info('Using "{}" to look up db info for "{}".'.format(att_key, new_att))
    formatted_sql_query = format_sql_query(sql_query, *arguments)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    log.info('Found {} results for this query.'.format(len(db_results)))

    # Make a db result dict.
    db_results_dict = build_uniq_db_result_dict(db_results)

    # Now add the info.
    add_cnt = 0
    for target in data_dict.values():
        # First confirm that the starting attribute exists.
        confirm_attribute(target, att_key)
        # Now get the db value and add it to new attribute (for dict or object).
        if type(target) == dict:
            this_key = get_dict_value(target, att_key)
            new_value = get_dict_value(db_results_dict, this_key)    # This could be return None, and that's OK.
            target[new_att] = new_value
            add_cnt += 1
        else:
            this_key = getattr(target, att_key)
            new_value = get_dict_value(db_results_dict, this_key)    # This could be return None, and that's OK.
            setattr(target, new_att, new_value)
            add_cnt += 1

    log.info('Added {} values to the {} attribute.\n'.format(add_cnt, new_att))

    return data_dict
