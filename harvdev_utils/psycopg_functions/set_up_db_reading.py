"""
.. module:: set_up_db_reading
   :synopsis: A module that performs general set up for scripts that connect to a FlyBase db and generate report files.
              Module parses command arguments, gets environmental variable values, connects to db, specifies filenames.

.. moduleauthor:: Gil dos Santos dossantos@morgan.harvard.edu
"""

import argparse
import configparser
import sys
import os
import psycopg2
import logging
import datetime
import strict_rfc3339
from ..general_functions import timenow
from ..psycopg_functions import establish_db_connection

log = logging.getLogger(__name__)


def set_up_db_reading(report_label):
    """
    Function that gets values for db connection, makes connection and specifies output filenames.
    Libraries:
        argparse, configparser, sys, os, psycopg2, datetime, logging, strict_rfc3339, alliance-flybase.utils.
    Other functions:
        establish_db_connection(), timenow().
    Args:
        A "report_label" string for the output files (logs and data).
    Returns:
        A dict of various values for the script.
    Raises:
        None.
    """

    log.info('TIME: {}. Setting up environment, db connections and logging.'.format(timenow()))

    # Parse command line inputs.
    parser = argparse.ArgumentParser(description='inputs')
    parser.add_argument('-v', '--verbose', action='store_true', help='DEBUG-level logging.', required=False)
    parser.add_argument('-c', '--config_file', help='Supply filepath to credentials, optional.', required=False)
    args = parser.parse_args()

    # Determine whether script is to run locally or in docker.
    config_file = args.config_file

    # Determine values for key variables.
    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)
        database_host = config['default']['Server']
        database = config['default']['Database']
        username = config['default']['User']
        password = config['default']['PGPassword']
        database_release = config['default']['Release']
        assembly = config['default']['Assembly']
        annotation_release = config['default']['AnnotationRelease']
        alliance_schema = config['default']['AllianceSchema']
        alliance_release = config['default']['AllianceRelease']
        # svn_username = config['default']['SVNUsername']
        # svn_password = config['default']['SVNPassword']
        output_dir = './'
    else:
        database_host = os.environ['SERVER']
        database = os.environ['DATABASE']
        username = os.environ['USER']
        password = os.environ['PGPASSWORD']
        database_release = os.environ['RELEASE']
        assembly = os.environ['ASSEMBLY']
        annotation_release = os.environ['ANNOTATIONRELEASE']
        alliance_schema = os.environ['ALLIANCESCHEMA']
        alliance_release = os.environ['ALLIANCERELEASE']
        # svn_username = os.environ['SVNUSER']
        # svn_password = os.environ['SVNPASSWORD']
        output_dir = '/src/output/'

    # Send values to a dict.
    set_up_dict = {}
    set_up_dict['database'] = database
    set_up_dict['database_release'] = database_release
    set_up_dict['assembly'] = assembly
    set_up_dict['annotation_release'] = annotation_release
    set_up_dict['alliance_schema'] = alliance_schema
    set_up_dict['alliance_release'] = alliance_release
    # set_up_dict['svn_username'] = svn_username
    # set_up_dict['svn_password'] = svn_password

    # Output filename
    set_up_dict['output_dir'] = output_dir
    set_up_dict['output_filename'] = output_dir + 'FB_' + alliance_schema + '_' + report_label + '.json'

    # Handle logging
    log_filename = output_dir + 'FB_' + alliance_schema + '_' + report_label + '.log'
    verbose = args.verbose
    if verbose is True:
        logging.basicConfig(format='%(levelname)s:%(message)s', filename=log_filename, level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', filename=log_filename, level=logging.INFO)
    sys.stdout = open(log_filename, 'a')
    set_up_dict['log'] = logging.getLogger(__name__)

    # Establish database connection.
    set_up_dict['conn'] = establish_db_connection(database_host, database, username, password)

    # Official timestamp for this script.
    set_up_dict['the_time'] = strict_rfc3339.now_to_rfc3339_localoffset()

    return set_up_dict
