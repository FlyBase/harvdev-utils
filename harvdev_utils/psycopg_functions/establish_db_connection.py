"""Module:: establish_db_connection.

Synopsis:
    Establishes a psycopg2 connection to a postgres db.

Author(s):
    Chris Tabone ctabone@morgan.harvard.edu, Gil dos Santos dossantos@morgan.harvard.edu

"""

import psycopg2
import logging

log = logging.getLogger(__name__)


def establish_db_connection(database_host, database, username, password):
    """Establish a connection to some postgres db.

    Args:
        arg1 (str): The "database_host" (server).
        arg2 (str): The "database" name.
        arg3 (str): The "username".
        arg4 (str): The postgres "password".

    Returns:
        psycopg2.extensions.connection: A psycopg2 database connection object.

    """
    conn_string = "host={} dbname={} user={} password='{}'".format(database_host, database, username, password)
    db_connection = psycopg2.connect(conn_string)
    conn_description = 'Made connection to database {} on db_host {}.'.format(database, database_host)

    return db_connection, conn_description
