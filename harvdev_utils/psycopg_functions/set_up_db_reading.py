"""Module:: set_up_db_reading.

Synopsis:
    A module that performs general set up for scripts that connect to a FlyBase db and generate report files.
    Module parses command arguments, gets environmental variable values, connects to db, specifies filenames.

Author(s):
    Gil dos Santos dossantos@morgan.harvard.edu, Julie Agapite jagapite@morgan.harvard.edu

"""

import argparse
import configparser
import sys
import os
import logging
import strict_rfc3339
from harvdev_utils.psycopg_functions import establish_db_connection

log = logging.getLogger(__name__)


def set_up_db_reading(report_label):
    """Get values db connection, makes connection and specifies output filenames.

    Args:
        arg1 (str): A "report_label" string for the output files (logs and data).

    Returns:
        dict: A dict of various values for the script to make db_connection, name files, etc.

    """
    # Parse command line inputs.
    parser = argparse.ArgumentParser(description='inputs')
    parser.add_argument('-v', '--verbose', action='store_true', help='DEBUG-level logging.', required=False)
    parser.add_argument('-a', '--alliance', action='store_true', help='Filenames for AGR export.', required=False)
    parser.add_argument('-c', '--config_file', help='Supply filepath to credentials, optional.', required=False)
    parser.add_argument('-t', '--testing', action='store_true', help='Rollback db writes.', required=False)
    # Use parse_known_args() instead of parse_args() to handle only the args relevant here without crashing.
    # Extra arguments that may be relevant to specific scripts using this module are safely ignored.
    # args = parser.parse_args()
    args, extra_args = parser.parse_known_args()

    # Determine whether script is to run locally or in docker.
    config_file = args.config_file

    # Determine values for key variables.
    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)
        server = config['default']['Server']
        database = config['default']['Database']
        username = config['default']['User']
        password = config['default']['PGPassword']
        database_release = config['default']['Release']
        assembly = config['default']['Assembly']
        annotation_release = config['default']['AnnotationRelease']
        alliance_schema = config['default']['AllianceSchema']
        alliance_release = config['default']['AllianceRelease']
        svn_username = config['default']['SVNUsername']
        svn_password = config['default']['SVNPassword']
        output_dir = './'
        log_dir = './'
    else:
        server = os.environ['SERVER']
        database = os.environ['DATABASE']
        username = os.environ['USER']
        password = os.environ['PGPASSWORD']
        database_release = os.environ['RELEASE']
        assembly = os.environ['ASSEMBLY']
        annotation_release = os.environ['ANNOTATIONRELEASE']
        alliance_schema = os.environ['ALLIANCESCHEMA']
        alliance_release = os.environ['ALLIANCERELEASE']
        svn_username = os.environ['SVNUSER']
        svn_password = os.environ['SVNPASSWORD']
        output_dir = '/src/output/'
        log_dir = '/src/logs/'

    # Send values to a dict.
    set_up_dict = {}
    set_up_dict['server'] = server
    set_up_dict['database'] = database
    set_up_dict['username'] = username
    set_up_dict['password'] = password
    set_up_dict['database_release'] = database_release
    set_up_dict['assembly'] = assembly
    set_up_dict['annotation_release'] = annotation_release
    set_up_dict['alliance_schema'] = alliance_schema
    set_up_dict['alliance_release'] = alliance_release
    set_up_dict['svn_username'] = svn_username
    set_up_dict['svn_password'] = svn_password
    set_up_dict['output_dir'] = output_dir

    # Determine if testing variable is True or false.
    set_up_dict['testing'] = args.testing

    # Output filename
    alliance = args.alliance
    if alliance is True:
        set_up_dict['output_filename'] = output_dir + 'FB_' + alliance_schema + '_' + report_label + '.json'
    else:
        set_up_dict['output_filename'] = output_dir + report_label + '_' + database + '.tsv'

    # Handle logging
    if alliance is True:
        log_filename = output_dir + 'FB_' + alliance_schema + '_' + report_label + '.log'
    else:
        log_filename = log_dir + report_label + '_' + database + '.log'
    file_handler = logging.FileHandler(log_filename, mode='a')
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : Line No %(lineno)d : %(message)s')
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    # Determine log level.
    verbose = args.verbose
    if verbose is True:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    sys.stdout = open(log_filename, 'a')
    set_up_dict['log'] = logging.getLogger(__name__)

    # Establish database connection.
    set_up_dict['conn'] = establish_db_connection(server, database, username, password)

    # Official timestamp for this script.
    set_up_dict['the_time'] = strict_rfc3339.now_to_rfc3339_localoffset()

    log.info('Done setting up the environment, db connections and logging.')
    if extra_args != []:
        log.info('These extra arguments were not used by set_up_db_reading(): {}'.format(extra_args))

    return set_up_dict
