"""Module:: write_proforma.

Synopsis:
    A module that takes data object (list of dicts) and writes it into a proforma record.
    The keys in the dicts must match the proforma field prefix (e.g., "G1a").
    For a given dict, it will match the prefixes to the correct proforma type (e.g., "GA" > ALLELE).
    The module grabs latest proforma templates from the SVN.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu

"""

import logging
import os
import re
import svn.remote
from harvdev_utils.general_functions import (
    timenow, today
)

log = logging.getLogger(__name__)


def get_p10_date(input_date):
    """Create proforma-compliant YYYY.M(M).D(D) date stamp from YYMMDD/YYYYMMDD input.

    Args:
        arg1 (str): A date string in YYMMDD or YYYYMMDD format.

    Returns:
        str: PUB proforma P10 field compliant YYYY.M.D date string.

    Raises:
        Will raise an exception if the input not a six or eight digit string.

    """
    # First check the input.
    if not re.match(r'(^[0-9]{6}$|^[0-9]{8}$)', input_date):
        log.error('Input string is not a six or eight digit string: {}'.format(input_date))
    # Get the year.
    if len(input_date) == 6:
        year = '20' + input_date[0:2]
    else:
        year = input_date[0:4]
    # Get the month, replacing leading zeroes.
    month = input_date[-4:-2].replace('0', '')
    # Get the day, replacing leading zeroes.
    day = input_date[-2:].replace('0', '')
    proforma_curation_date = year + '.' + month + '.' + day

    return proforma_curation_date


def get_proforma_masters(svn_username, svn_password, get_remote):
    """Get all proforma masters from SVN and return a dictionary keyed by proforma type, then by field.

    Args:
        arg1 (svn_username): (str) SVN username.
        arg2 (svn_password): (str) SVN password.
        arg3 (get_remote): (bool) If True, gets SVN from URL, else looks in /src/input/.

    Returns:
        dict: A nested dict with level one keys corresponding to proforma types (extracted from filenames).
              The level two keys correspond to proforma field prefixes: e.g., "G1a", "SF2b".
              e.g., {
                        'gene':
                            {
                                'G1h': '! G1h.  FlyBase gene ID (FBgn) *z :',
                                'G1b': '! G1a.  Gene symbol to use in FlyBase  *a :',
                                ...
                            },
                        'allele':
                            {
                                'GA1a': ...
                    }
    """
    log.info('TIME: {}. Retrieving proforma masters.'.format(timenow()))
    if get_remote is True:
        svn_url = 'https://svn.flybase.org/documents/curation/proformae/'
        r = svn.remote.RemoteClient(svn_url, username=svn_username, password=svn_password)
        local_svn_path = '/tmp/working/'
        r.checkout(local_svn_path)
    else:
        local_svn_path = '/src/input/'
    svn_contents = os.scandir(local_svn_path)
    proforma_master_dict = {}
    proforma_master_dict = {}
    for item in svn_contents:
        if item.name.endswith('_master.pro'):
            pro_path = local_svn_path + item.name
            pro_name = item.name.split('_')[0]
            log.debug('Assessing the {} proforma now.'.format(pro_name))
            proforma_master_dict[pro_name] = {}
            pro_contents = open(pro_path, 'rt')
            line_counter = 0
            for line in pro_contents:
                # Look for header
                if re.match(r'! [A-Z]{3}.*Version.*[0-9]{4}\n$', line):
                    proforma_master_dict[pro_name]['header'] = line.rstrip()
                    log.debug('Found "header": {}'.format(proforma_master_dict[pro_name]['header']))
                    line_counter += 1
                # Look for proforma field leader.
                elif re.match(r'!\s{1,6}[A-Z]{1,3}[0-9]{1,2}[a-z]{0,1}\.', line):
                    left_line = re.match(r'!\s{1,6}[A-Z]{1,3}[0-9]{1,2}[a-z]{0,1}\.', line).group(0)
                    field_tag = re.search(r'(?<=\s)[A-Z]{1,3}[0-9]{1,2}[a-z]{0,1}', left_line).group(0)
                    field = line.split(':')[0] + ':'
                    proforma_master_dict[pro_name][field_tag] = field
                    log.debug('Found tag: {}, line: {}'.format(field_tag, field))
                    line_counter += 1
                # Look for end of proforma. If found, stop reading.
                # e.g., EXPRESSION proforma has curation manual after proforma template.
                elif re.match(r'!!', line):
                    proforma_master_dict[pro_name]['end'] = 80 * '!'
                    log.debug('Found end of proforma template.')
                    line_counter += 1
                    break
                # Ignore other stuff in proforma.
                else:
                    log.debug('Ignore this proforma master line: {}'.format(line.rstrip()))
                    line_counter += 1
            # Get distinguishing field tag prefix for this proforma master (e.g., "GA" for ALLELE).
            field_tag_count = len(proforma_master_dict[pro_name].keys())
            log.debug('Found {} field tags in {} lines for {}'.format(field_tag_count, line_counter, pro_name))
    # Check the master proforma if in debug.
    log.debug('Checking master proforma.')
    for pro_type in proforma_master_dict.keys():
        for k, v in proforma_master_dict[pro_type].items():
            log.debug('{}; {}; {}'.format(pro_type, k, v))

    return proforma_master_dict


def get_distinct_proforma_field_prefixes(all_proforma_dict):
    """Make a field tag prefix to proforma type dict for detection of proforma type.

    Args:
        arg1 (dict): The nested proforma dict (proforma_type > field prefix) generated by get_proforma_masters().

    Returns:
        dict: A dictionary of distinct field tag prefix to proforma type. Used for detect_proforma_type().
              e.g., {"G": "gene", "GA": "allele", ...}

    Warnings:
        Will raise a warning if a given proforma type has > 1 field prefix string: e.g., expect only "G" for GENE.

    """
    log.info('TIME: {}. Identifying unique field prefix tag for proforma masters.'.format(timenow()))
    field_to_proforma_dict = {}
    # Look through each type of proforma in the input "all_proforma_dict".
    for pro_type in all_proforma_dict.keys():
        log.debug('Assessing proforma type: {}'.format(pro_type))
        pro_dict = all_proforma_dict[pro_type]
        # A list for collecting all unique field prefixes for a given proforma type: e.g., "G" for all GENE fields.
        field_tag_prefixes = []
        for key in pro_dict.keys():
            try:
                field_tag_prefix = re.match(r'[A-Z]{1,3}', key).group(0)
                field_tag_prefixes.append(field_tag_prefix)
            except AttributeError:
                log.debug('Ignoring this proforma key: {}'.format(key))
        # Get the unique set of field prefixes for a given proforma.
        distinct_field_tag_prefixes = list(set(field_tag_prefixes))
        distinct_field_count = len(distinct_field_tag_prefixes)
        # We're expecting only one type of field prefix per proforma type: e.g., "G" for GENE, "GA" for ALLELE.
        if distinct_field_count == 1:
            field_prefix = distinct_field_tag_prefixes[0]
            log.debug('The {} master has this distinct field tag prefix: {}'.format(pro_type, field_prefix))
            field_to_proforma_dict[field_prefix] = pro_type
        # However, if we get multiple field types, we can't make the correspondence.
        # We add this to the dict for our records - would probably warrant fix to code or pro template.
        else:
            field_prefix = 'undetermined for ' + pro_type
            log.warning('The {} master has {} distinct field tag prefixes.'.format(pro_type, distinct_field_count))
            field_to_proforma_dict[field_prefix] = pro_type
    # For debugging, print this dict to the log file.
    for k, v in field_to_proforma_dict.items():
        log.debug('Field tag prefix {} corresponds to this proforma type: {}'.format(k, v))

    return field_to_proforma_dict


def detect_proforma_type(data_object, field_to_proforma_dict):
    """Detect the proforma type for a given data object (dict) by that object's keys.

    Args:
        arg1 (dict): The data object which encodes values for proforma record, keyed by proforma field prefix.
        arg2 (dict): The field-prefix-to-proforma-type dict generated by get_distinct_proforma_field_prefixes().

    Returns:
        str: Will be "undetermined", or the name of the proforma type (extracted from SVN proforma template file name).
             If a name, it will match the keys in the master proforma dict generated by get_proforma_masters().
             The "undetermined" is returned if: 1) "data_object" is not a dict; 2) 0 or many types detected.

    Warnings:
        Will raise a warning if a data_object key does not match any known proforma field prefix.
    """
    log.debug('TIME: {}. Detecting proforma type for this object: {}'.format(timenow(), data_object))
    # First make sure it's a dictionary.
    if type(data_object) != dict:
        log.warning('Data object is not of expected type dictionary.')
        resolved_proforma_type = 'undetermined'
    # Scan the dictionary keys.
    proforma_types_detected = []
    for key in data_object:
        if re.match(r'[A-Z]{1,3}', key):
            try:
                key_prefix = re.match(r'[A-Z]{1,3}', key).group(0)
                proforma_type = field_to_proforma_dict[key_prefix]
                log.debug('Key "{}" corresponds to proforma type: {}'.format(key, proforma_type))
                proforma_types_detected.append(proforma_type)
            except KeyError:
                log.warning('Key "{}" looks like a proforma field prefix but is unknown.'.format(key))
        else:
            log.debug('Ignoring key "{}"'.format(key))
    # Unique the types of proforma detected for data object.
    # We expect that a data_object dict corresponds to only one type of proforma; otherwise, code does nothing.
    proforma_types_detected = list(set(proforma_types_detected))
    cnt_types = len(proforma_types_detected)
    if cnt_types == 0:
        log.warning('Detected no proforma types for this object.')
        resolved_proforma_type = 'undetermined'
    elif cnt_types > 1:
        log.warning('Cannot process data object representing many proforma types.')
        for i in proforma_types_detected:
            log.warning(i)
        resolved_proforma_type = 'undetermined'
    else:
        resolved_proforma_type = proforma_types_detected[0]
        log.debug('This data object corresponds to this proforma type: {}'.format(resolved_proforma_type))

    return resolved_proforma_type


def write_record_curation_header(svn_username, outfile):
    """Write out curation header for HarvCur proforma records to some output file.

    Args:
        arg1 (str): The SVN username that is used to look up the curator initials.
        arg2 (_io.TextIOWrapper): An output file object for writing to.

    Returns:
        None.

    """
    # Hash for users and related initials.
    user_hash = {
        'dossantos': 'gds',
        'crosby': 'lc',
        'ctabone': 'ct',
        'bmatthew': 'bev',
        'gramates': 'sian',
        'jagapite': 'jma',
        'vjenkins': 'vj',
        'go': 'go',
        'unspecified': 'go',
    }
    curator_initials = user_hash[svn_username]
    this_day = today()
    curation_header = '! C1.  Curator ID  :{}\n! C2.  Date        :{}\n'.format(curator_initials, this_day)
    outfile.write(curation_header)
    outfile.write('!' * 80 + '\n')

    return


def write_record_end(outfile):
    """Write out the record ending.

    Args:
        arg1 (_io.TextIOWrapper): An output file object for writing to.

    Returns:
        None.

    """
    outfile.write('!' * 22 + ' END OF RECORD FOR THIS PUBLICATION ' + '!' * 22)

    return


def write_proforma_line(field_key, field_value, proforma, outfile):
    """Evaluate a specific key:value pair in a data object and write proforma line(s) to file.

    Args:
        arg1 (str): The proforma field key.
        arg2: The value in the data object for a given key. Different object types are processed.
        arg3 (dict): The dict representing a specific proforma type (keys match field prefixes: e.g., "G1a").
        arg4 (_io.TextIOWrapper): An output file object for writing to.

    Returns:
        None.

    """
    log.debug('TIME: {}. Writing proforma line to file.'.format(timenow()))
    # Make sure data_object key is also in proforma key. Other keys are ignored.
    if field_key not in proforma.keys():
        log.warning('Ignoring {}: {}. Proforma key not recognized.'.format(field_key, field_value))
    # Action depends on type of value for a given key.
    # Value can be str, int, float, dict or monotypic list/tuple of any of these.
    # Simple case is when value is single str, int or float.
    elif type(field_value) in [str, int, float]:
        outfile.write(proforma[field_key])
        outfile.write(field_value + '\n')
    # If it's a list, evaluate each element in turn.
    elif type(field_value) in [list, tuple]:
        # Determine if list/tuple is monotypic.
        # Code doesn't handle a list of different element types.
        list_types = list(set(type(i) for i in field_value))
        if len(list_types) != 1:
            log.warning('Ignoring {}: {}. Cannot handle empty or mixed lists.'.format(field_key, field_value))
        # If it's a list of str/int/float, just write each element of the list out after the proforma leader.
        # e.g., list multiple synonyms on separate lines after writing G1b leader once.
        elif list_types[0] in [str, int, float]:
            log.debug('Handling {}: {} as list/tuple of {} objects.'.format(field_key, field_value, list_types[0]))
            outfile.write(proforma[field_key])
            for item in field_value:
                outfile.write(item + '\n')
        # If it's a list of dicts, just write out each element of each dict in turn.
        # In this way, one can write multiple sets of proforma fields: e.g., LC99a/LC99b accession/db pairs.
        #     { "LC99a": [ { "LC99a": "acc1", "LC99b": "db1" }, { "LC99a": "acc2", "LC99b": "db2" },...] }
        elif list_types[0] == dict:
            log.debug('Handling {}: {} as a list/tuple of dict objects.'.format(field_key, field_value))
            for element_dict in field_value:
                for element_key, element_value in element_dict.items():
                    write_proforma_line(element_key, element_value, proforma, outfile)
        else:
            log.warning('Ignoring {}: {}. Cant handle value type: {}.'.format(field_key, field_value, list_types[0]))
    else:
        log.warning('Ignoring {}: {}. Cant handle value of type: {}.'.format(field_key, field_value, type(field_value)))

    return


def write_proforma_stanza(data_object, proforma, outfile):
    """Write proforma stanza for a given data_object.

    Args:
        arg1 (dict): The data object to write.
        arg2 (dict): The proforma type that corresponds to the data object.
        arg3 (_io.TextIOWrapper): An output file object for writing to.

    Returns:
        None.

    """
    log.debug('TIME: {}. Writing proforma stanza to file.'.format(timenow()))
    # Write out header.
    outfile.write(proforma['header'] + '\n')
    # Write out lines of proforma stanza.
    for field_key in data_object.keys():
        field_value = data_object[field_key]
        write_proforma_line(field_key, field_value, proforma, outfile)
    # Write stanza closer.
    outfile.write(proforma['end'] + '\n')

    return


def write_proforma_record(data_list, output_filename, svn_username, svn_password, get_remote):
    """Write full proforma record for a list of dicts representing data objects.

    A wrapper of several smaller functions in the "write_proforma" module.
    Expects that the data_list will be a list of dicts.
    List order determines write order.
    Each dict is expected to represent only a single proforma type; otherwise skipped.

    Args:
        arg1 (data_list): (list) The list of data objects to write to file.
        arg2 (output_filename): (str) The filename of the output file.
        arg3 (svn_username): (str) The SVN username.
        arg4 (svn_password): (str) The SVN password.
        arg5 (get_remote): (bool) If true, gets SVN info remotely, else, looks in /src/input/.

    Returns:
        None.

    """
    log.info('TIME: {}. Writing proforma record to "{}".'.format(timenow(), output_filename))
    outfile = open(output_filename, 'wt')

    master_proforma_dict = get_proforma_masters(svn_username, svn_password, get_remote)
    field_to_proforma_dict = get_distinct_proforma_field_prefixes(master_proforma_dict)
    write_record_curation_header(svn_username, outfile)
    for datum in data_list:
        proforma_type = detect_proforma_type(datum, field_to_proforma_dict)
        if proforma_type != 'undetermined':
            data_type_specific_proforma_dict = master_proforma_dict[proforma_type]
            write_proforma_stanza(datum, data_type_specific_proforma_dict, outfile)
    write_record_end(outfile)

    return
