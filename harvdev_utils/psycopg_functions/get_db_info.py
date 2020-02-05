"""
.. module:: get_db_info
   :synopsis: gets bulk data from db to create new object, or add info to an exising object.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import psycopg2
import logging
import datetime
from ..general_functions import timenow
from ..psycopg_functions import connect, current_features, Feature, Allele, Construct, Gene, Insertion, SeqFeat, Tool

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
    result_cnt = len(db_results)
    log.info('Found {} results for this query.'.format(result_cnt))

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
        Will raise an exception if multiple values are found for a given "data_dict" key.
        For example, each gene should have only one current symbol synonym.
        An exception will be raised if trying to add a 2nd value to some key's attribute.
    """

    # Perform the query.
    log.info('TIME: {}. Adding unique db info to this attribute: {}'.format(timenow(), attribute))
    formatted_sql_query = sql_query.format(*arguments)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    result_cnt = len(db_results)
    log.info('Found {} results for this query.'.format(result_cnt))

    # Check there's only one row per "db_results" key (i.e, row's first value).
    db_keys = set([row[0] for row in db_results])
    if len(db_keys) < result_cnt:
        raise ValueError('Getting many values per key. Try "add_list_info" function instead.')

    # Check for overlap in db_result and data_dict keys.
    key_overlap = set(data_dict.keys()).intersection(db_keys)
    if key_overlap == 0:
        log.warning('There is no overlap between the data_dict keys and the db results keys.')

    # Now add the results.
    add_cnt = 0
    for row in db_results:
        key = row[0]
        try:
            target = data_dict[key]
        except KeyError:
            log.debug('The db results key "{}" does not exist in the target data_dict.'.format(key))
            continue
        if len(row) > 2:
            result = tuple(row[1:])
        else:
            result = row[1]
        # Action depends on whether info is being added to a dict or some other object type.
        if type(target) == dict:
            try:
                target[attribute] = result
                add_cnt += 1
            except KeyError:
                raise KeyError('Attribute {} not found as key for the target data object.'.format(attribute))
        else:
            try:
                setattr(target, attribute, result)
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
    formatted_sql_query = sql_query.format(*arguments)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    result_cnt = len(db_results)
    log.info('Found {} results for this query.'.format(result_cnt))

    # Check for overlap in db_result and data_dict keys.
    db_keys = set([row[0] for row in db_results])
    key_overlap = set(data_dict.keys()).intersection(db_keys)
    if len(key_overlap) == 0:
        log.warning('There is no overlap between the data_dict keys and the db results keys.')
    else:
        log.debug('{} db results overlap with data_dict keys.'.format(len(key_overlap)))

    # Set targeted attribute to an empty list if None.
    # This indicates attribute has been evaluated; an empty list means results sought but none found.
    # If still None, then results not yet sought.
    for key, target in data_dict.items():
        empty_list = []
        if type(target) == dict:
            try:
                if target[attribute] is None:
                    target[attribute] = empty_list
                    log.debug('Before adding values, attribute {} set to this: {}.'.format(attribute, empty_list))
            except KeyError:
                raise KeyError('Attribute {} not found as key for the target data object.'.format(attribute))
        else:
            try:
                if getattr(target, attribute) is None:
                    setattr(target, attribute, empty_list)
                    log.debug('Before adding values, attribute {} set to this: {}.'.format(attribute, empty_list))
            except AttributeError:
                raise AttributeError('Attribute {} not found for the target data object.'.format(attribute))

    # Now add the results.
    add_cnt = 0
    # Build a dict of the db results (grouping lines by key).
    db_results_dict = {}
    for row in db_results:
        key = row[0]
        if len(row) > 2:
            row_result = tuple(row[1:])
        else:
            row_result = row[1]
        log.debug('For key: {}; have result: {}'.format(key, row_result))
        if key in db_results_dict.keys():
            db_results_dict[key].append(row_result)
        else:
            db_results_dict[key] = [row_result]
    log.debug(db_results_dict)
    # Integrate into data_dict.
    for key, db_value in db_results_dict.items():
        log.debug('Trying to add this: {}: {}'.format(key, db_value))
        try:
            target = data_dict[key]
        except KeyError:
            log.debug('The db results key "{}" does not exist in the target data_dict.'.format(key))
            continue
        # Action depends on whether info is being added to a dict or some other object type.
        if type(target) == dict:
            log.debug('The target object is a dict.')
            try:
                target[attribute].extend(db_value)
                add_cnt += 1
            except KeyError:
                raise KeyError('Attribute {} not found as key for the target data object.'.format(attribute))
        else:
            log.debug('The target object is not a dict.')
            try:
                target_value = getattr(target, attribute)
                log.debug('Have this current value: {}'.format(target_value))
                target_value.extend(db_value)
                target_value = getattr(target, attribute)
                log.debug('Have this updated value: {}'.format(target_value))
                # setattr(target, attribute, new_value)
                add_cnt += 1
            except AttributeError:
                raise AttributeError('Attribute {} not found for the target data object.'.format(attribute))

    log.info('TIME: {}. Added values to the {} attribute of {} objects.\n'.format(timenow(), attribute, add_cnt))

    return data_dict


def add_unique_dict_info(data_dict, att_key, att_value, db_connection, sql_query, *arguments):
    """
    For a data_dict, this function adds db values to each keyed-object.
    For each object, this function uses one attribute to look up the value for a 2nd attribute.
    For example, given an allele.organism_id, look up the allele.org_abbr (1 => 'Dmel').
    The look up dict is generated by sql query, where column 1 values should match up to "att_key" values.
    The rest of the db result columns go into the 2nd "att_value" attribute that is being updated.
    Will add single values or tuples (if db result rows have > 2 elements).
    Libraries:
        psycopg2, logging, datetime, alliance-flybase.utils.
    Other functions:
        None.
    Args:
        The input "data_dict", the "att_key" for look ups, and the "att_value" where updated info goes.
        A "db_connection", an "sql_query" string, and a list of "*arguments" to add into the query string.
    Returns:
        The same "data_dict", but now with extra information in the "att_value" field specified.
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
    log.info('TIME: {}. Using "{}" to look up db info for "{}".'.format(timenow(), att_key, att_value))
    formatted_sql_query = sql_query.format(*arguments)
    log.debug('Using this query string: {}'.format(formatted_sql_query))
    db_results = connect(formatted_sql_query, 'no_query', db_connection)
    result_cnt = len(db_results)
    log.info('Found {} results for this query.'.format(result_cnt))

    # Make a db result dict.
    db_dict = {}
    if len(db_results[0]) < 2:
        raise ValueError('Need at least two columns of db results.')
    elif len(db_results[0]) == 2:
        add_tuples = False
    else:
        add_tuples = True
    for row in db_results:
        key = row[0]
        if add_tuples is False:
            value = row[1]
        else:
            value = tuple(row[1:])
        db_dict[key] = value

    # Check that there's only one value per key, since expectation is only one unique value in db.
    if len(db_dict.keys()) < result_cnt:
        raise ValueError('Getting many values per key. Try "add_list_dict_info" function instead.')

    # Now add the info.
    add_cnt = 0
    for item in data_dict.values():
        if type(item) == dict:
            try:
                this_key = item[att_key]
            except KeyError:
                raise KeyError('Object has no attribute "{}".'.format(att_key))
            try:
                this_value = db_dict[this_key]
            except KeyError:
                log.warning('For {}, no db result found for "att_key": {}.'.format(att_key, this_key))
                this_value = None
            try:
                item[att_value] = this_value
                add_cnt += 1
            except KeyError:
                raise KeyError('Object has no attribute "{}".'.format(att_value))
        else:
            try:
                this_key = getattr(item, att_key)
            except AttributeError:
                raise AttributeError('Object has no attribute "{}".'.format(att_key))
            try:
                this_value = db_dict[this_key]
            except KeyError:
                log.warning('For {}, no db result found for "att_key": {}.'.format(att_key, this_key))
                this_value = None
            try:
                setattr(item, att_value, this_value)
                add_cnt += 1
            except AttributeError:
                raise AttributeError('Object has no attribute "{}".'.format(att_value))

    log.info('TIME: {}. Added {} values to the {} attribute.\n'.format(timenow(), add_cnt, att_value))

    return data_dict
