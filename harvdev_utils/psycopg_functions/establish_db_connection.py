"""
.. module:: establish_db_connection
   :synopsis: Establishes a psycopg2 connection to a postgres db.

.. moduleauthor:: Chris Tabone ctabone@morgan.harvard.edu, Gil dos Santos dossantos@morgan.harvard.edu
"""

import psycopg2
import logging
import datetime
from ..general_functions import timenow

log = logging.getLogger(__name__)


def establish_db_connection(database_host, database, username, password):
    """
    Function that establishes the database connection.
    Libraries:
        psycopg2, datetime, logging, alliance-flybase.utils.
    Other functions:
        timenow().
    Args:
        A "database_host" (server), "database", "username", and "password".
    Returns:
        A database connection object.
    Raises:
        None.
    """

    conn_string = "host={} dbname={} user={} password='{}'".format(database_host, database, username, password)
    db_connection = psycopg2.connect(conn_string)

    log.info('TIME: {}. Made connection to database {} on host {}.'.format(timenow(), database, database_host))

    return db_connection
