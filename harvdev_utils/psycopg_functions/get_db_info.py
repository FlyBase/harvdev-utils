"""
.. module:: get_db_info
   :synopsis: gets bulk data from db to create new object, or add info to an exising object.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

# import psycopg2
import logging
# import datetime
from ..general_functions import timenow
from ..psycopg_functions import (
    connect, current_features, Allele, Construct, Gene, Insertion, SeqFeat, Tool
)

log = logging.getLogger(__name__)


def get_features(db_connection, feat_regex):
    """
    Gets all current, non-analysis features for a given uniquename regex.
    Returns a FB-uniquename-keyed dict of Feature-type objects.
    Libraries:
        psycopg2, re, logging, datetime, alliance-flybase.utils.
    Classes:
        Feature (and its children).
    Functions:
        connect(), timenow().
    Args:
        The "db_connection", the feature uniquename "feat_regex".
    Returns:
        FB-uniquename-keyed dict/hash of appropriate Feature-class objects.
    Raises:
        If Feature-type Object to use cannot be determined from the prefix.
    """
    log.info('TIME: {}. Getting FlyBase features having uniquename like "{}".'.format(timenow(), feat_regex))
    formatted_sql_query = current_features.format(feat_regex)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    log.info('Found {} results for this query.'.format(len(db_results)))

    ThisFeature = None
    class_dict = {
        'FBal': Allele,
        'FBtp': Construct,
        'FBgn': Gene,
        'FBti': Insertion,
        'FBsf': SeqFeat,
        'FBto': Tool
    }
    for prefix in class_dict:
        if prefix in feat_regex:
            ThisFeature = class_dict[prefix]
    if ThisFeature is None:
        raise TypeError('Cound not determine Feature-type Object to use.')

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

    log.info('TIME: {}: Returning feature dict with {} entries.\n'.format(timenow(), len(feature_dict.keys())))

    return feature_dict


def confirm_attribute(item, attribute):
    """
    For some item (object or dictionary), checks that an attribute exists.
    Libraries:
        logging.
    Other functions:
        None.
    Args:
        An object or dictionary.
    Returns:
        None.
    Warnings:
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
    """
    For some dict and key, gets the value. Returns None if no value to get.
    Args:
        A dictionary and some look-up key.
    Returns:
        The value for a key, it if exists. Otherwise, returns None.
    """
    try:
        this_value = this_dict[this_key]
    except KeyError:
        log.debug('Dictionary has no attribute: {}. Returning "None"'.format(this_key))
        this_value = None

    return this_value


def format_sql_query(sql_query, *arguments):
    """
    For an sql_query and an optional list of arguments, it formats text of an sql query.
    Libraries:
        None.
    Other functions:
        format().
    Args:
        An input string with optional "{}" placeholders for format.
    Returns:
        A formatted sql query that combines query with arguments.
    Warnings:
        None.
    Raises:
        None.
    """

    if len(arguments) == 0:
        formatted_sql_query = sql_query
    else:
        formatted_sql_query = sql_query.format(*arguments)

    return formatted_sql_query


def check_unique_results(db_results):
    """
    For some set of db results, this query checks if keys (column 1 values) appear only once and are thus unique.
    Libraries:
        None.
    Other functions:
        None.
    Args:
        A list of lists (sql db results).
    Returns:
        Nothing.
    Warnings:
        None.
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
    """
    For a FB-ID-keyed data_dict and db_results, checks overlap of ID keys with db_results column one values.
    Libraries:
        logging.
    Other functions:
        None
    Args:
        A data_dict and some db_results from psycopg2.
    Returns:
        Nothing.
    Warnings:
        Raises a warning if there is no overlap in keys.
    Raises:
        None.
    """

    data_keys = set(data_dict.keys())
    db_keys = set([row[0] for row in db_results])
    key_overlap = set(data_keys.intersection(db_keys))
    if len(key_overlap) == 0:
        log.warning('There is no overlap between the data_dict keys and the db results keys.')

    return


def get_key_value(row):
    """
    For some list (usually sql result row), determines key and value pair.
    Key is element in first column. Value depends on number of columsn in row ("n").
    Value is element in second column if n = 2 columns.
    Value is tuple of columns 2-n if n > 2 columns.
    Libraries:
        None.
    Other functions:
        None.
    Args:
        A list (usually of row from an sql query result).
    Returns:
        Two variables - the "row_key" and "row_value".
    Warnings:
        None.
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
    """
    For some db_results, converts into a dictionary.
    Dict key will be column 1 element; dict value will be column2 or tuple of columns 2-n.
    Libraries:
        None.
    Other functions:
        check_unique_results(), get_key_value()
    Args:
        A set of db_results for psycopg2 (list of lists).
    Returns:
        A dict where keys are column 1 values and results are columns 2-n values.
    Warnings:
        None.
    Raises:
        None in addition to those in sub-functions used.
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
    """
    For some db_results, converts into a dictionary.
    Dict key will be column 1 element; dict value will be a list of values.
    Values in that list will be column2 or tuple of columns 2-n, depending on row length.
    Libraries:
        None.
    Other functions:
        get_key_value()
    Args:
        A set of db_results for psycopg2 (list of lists).
    Returns:
        A dict where keys are column 1 values and each result is a list.
        If row has two columns, list has single elements corresponding to column 2.
        If row has "n" columns where n >2, values are tuples of columns 2-n values.
    Warnings:
        None.
    Raises:
        None.
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
    """
    For some keyed dict, it will construct an sql query (with args given), query db and return results.
    Those results added into data_dict by matching keys, assigned to the "attribute" specified.
    The keyed object can itself be a dict, in which case the "attribute" must match a key.
    If the keyed object is something else, it must have an attribute matching the one specified.
    Will add single values or tuples (if db result rows have > 2 elements).
    This "add_unique_info" function is similar to the "add_list_info" function.
    Libraries:
        psycopg2, logging, datetime, alliance-flybase.utils.
    Other functions:
        get_key_value(), format_sql_query(), check_unique_results(), check_key_overlap(), timenow(), connect().
    Args:
        The input "data_dict", and the name of the "attribute" to which new info is to be added
        A "db_connection", an "sql_query" string, and a list of "*arguments" to add into the query string.
    Returns:
        The same "data_dict", but now with extra information in the "attribute" field specified.
        If db results have only 2 columns (key plus one piece of info), adds that piece of info.
        If db results have > 2 columns, add columns after the key (first column) as a tuple.
    Warnings:
        Warns if there is no overlap between "data_dict" keys and db results keys (first value in each result row).
        However, it quietly skips over cases where db data key is not a data_dict key ...
        ... since we expect cases where scope of results is greater than data_dict.
    Raises:
        Will raise an exception if given attribute is not found for the data_dict's keyed value.
        Will raise an exception if multiple values are found for a given "data_dict" key.
        For example, each gene should have only one current symbol synonym.
        An exception will be raised if trying to add a 2nd value to some key's attribute.
    """

    # Perform the query.
    log.info('TIME: {}. Adding unique db info to this attribute: {}'.format(timenow(), attribute))
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
        confirm_attribute(data_dict, row_key)
        try:
            target = data_dict[row_key]
        except KeyError:
            log.debug('The db results key "{}" does not exist in the target data_dict.'.format(row_key))
            continue
        # Action depends on whether info is being added to a dict or some other object type.
        if type(target) == dict:
            try:
                target[attribute] = row_value
                add_cnt += 1
            except KeyError:
                raise KeyError('Attribute {} not found as key for the target data object.'.format(attribute))
        else:
            try:
                setattr(target, attribute, row_value)
                add_cnt += 1
            except AttributeError:
                raise AttributeError('Attribute {} not found for the target data object.'.format(attribute))

    log.info('TIME: {}. Added {} values to the {} attribute.\n'.format(timenow(), add_cnt, attribute))

    return data_dict


def add_list_info(data_dict, attribute, db_connection, sql_query, *arguments):
    """
    For some keyed dict, it will construct an sql query (with args given), query db and return results.
    Those results added into data_dict by matching keys, assigned to the "attribute" specified.
    The keyed object can itself be a dict, in which case the "attribute" must match a key.
    If the keyed object is something else, it must have an attribute matching the one specified.
    Will add single values or tuples (if db result rows have > 2 elements).
    This "add_list_info" function is similar to the "add_unique_info" function.
    Libraries:
        psycopg2, logging, datetime, alliance-flybase.utils.
    Other functions:
        None.
    Args:
        The input "data_dict", and the name of the "attribute" to which new info is to be added
        A "db_connection", an "sql_query" string, and a list of "*arguments" to add into the query string.
    Returns:
        The same "data_dict", but now with extra information in the "attribute" field specified.
        If db results have only 2 columns (key plus one piece of info), adds that piece of info.
        If db results have > 2 columns, add columns after the key (first column) as a tuple.
    Warnings:
        Warns if there is no overlap between "data_dict" keys and db results keys (first value in each result row).
        However, it quietly skips over cases where db data key is not a data_dict key ...
        ... since we expect cases where scope of results is greater than data_dict.
    Raises:
        Will raise an exception if given attribute is not found for the data_dict's keyed value.
    """

    # Perform the query.
    log.info('TIME: {}. Adding list of db info to this attribute: {}'.format(timenow(), attribute))
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

    log.info('TIME: {}. Added values to the {} attribute of {} objects.\n'.format(timenow(), attribute, add_cnt))

    return data_dict


def add_unique_dict_info(data_dict, att_key, new_att, db_connection, sql_query, *arguments):
    """
    For a data_dict, this function adds db values to each keyed-object.
    For each object, this function uses one attribute to look up the value for a 2nd attribute.
    For example, given an allele.organism_id, look up the allele.org_abbr (1 => 'Dmel').
    The look up dict is generated by sql query, where column 1 values should match up to "att_key" values.
    The rest of the db result columns go into the 2nd "new_att" attribute that is being updated.
    Will add single values or tuples (if db result rows have > 2 elements).
    Libraries:
        psycopg2, logging, datetime, alliance-flybase.utils.
    Other functions:
        get_key_value(), format_sql_query(), check_unique_results(), check_key_overlap(), timenow(), connect().
        confirm_attribute().
    Args:
        The input "data_dict", the "att_key" for look ups, and the "new_att" where updated info goes.
        A "db_connection", an "sql_query" string, and a list of "*arguments" to add into the query string.
    Returns:
        The same "data_dict", but now with extra information in the "new_att" field specified.
        If db results have only 2 columns (key plus one piece of info), adds that piece of info.
        If db results have > 2 columns, add columns after the key (first column) as a tuple.
    Warnings:
        Warns if there is no overlap between "data_dict" keys and db results keys (first value in each result row).
        However, it quietly skips over cases where db data key is not a data_dict key ...
        ... since we expect cases where scope of results is greater than data_dict.
    Raises:
        Will raise an exception if db results have 0 or 1 columns.
        Will raise an exception if many values per key, since expect only one unique db value per key.
        For example, each gene should have only one current symbol synonym.
    """

    # Perform the query.
    log.info('TIME: {}. Using "{}" to look up db info for "{}".'.format(timenow(), att_key, new_att))
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

    log.info('TIME: {}. Added {} values to the {} attribute.\n'.format(timenow(), add_cnt, new_att))

    return data_dict
