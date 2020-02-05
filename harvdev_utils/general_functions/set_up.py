"""
.. module:: get_env_variables
   :synopsis: A module that parses command line arguments and gets values for needed environmental variables.

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
from general_functions import timenow
from ..psycopg_functions import establish_db_connection

log = logging.getLogger(__name__)


def set_up(report_label):
    """
    Function that establishes the database connection.
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
    parser = argparse.ArgumentParser(description='inputs')
    parser.add_argument('-v', '--verbose', action='store_true', help='DEBUG-level logging.', required=False)
    parser.add_argument('-l', '--local', action='store_true', help='Use local credentials.', required=False)
    args = parser.parse_args()

    # Determine whether script is to run locally or in docker.
    local = args.local
    if local is True:
        config = configparser.ConfigParser()
        config.read('/data/credentials/alliance/connection_info.cfg')
        database_host = config['default']['DatabaseHost']
        database = config['default']['Database']
        username = config['default']['Username']
        password = config['default']['Password']
        assembly = config['default']['Assembly']
        annotation_release = config['default']['AnnotationRelease']
        database_release = config['default']['DatabaseRelease']
        alliance_schema = config['default']['AllianceSchema']
        output_dir = './'
    else:
        database_host = os.environ['SERVER']
        database = os.environ['DATABASE']
        username = os.environ['USER']
        password = os.environ['PGPASSWORD']
        assembly = os.environ['ASSEMBLY']
        annotation_release = os.environ['ANNOTATIONRELEASE']
        database_release = os.environ['DATABASERELEASE']
        alliance_schema = os.environ['ALLIANCESCHEMA']
        output_dir = '/src/output/'

    set_up_dict = {}
    set_up_dict['assembly'] = assembly
    set_up_dict['annotation_release'] = annotation_release
    set_up_dict['database_release'] = database_release
    set_up_dict['alliance_schema'] = alliance_schema
    set_up_dict['output_dir'] = output_dir

    # Specify output filename.
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
