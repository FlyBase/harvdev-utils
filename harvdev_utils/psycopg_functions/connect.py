"""
.. module:: connect
   :synopsis: Queries a postgres db by a psycopg2 connection.

.. moduleauthor:: Chris Tabone ctabone@morgan.harvard.edu
"""

# import psycopg2


def connect(sql, query_variable, db_connection):
    """
    Function that retrieves information from a postgres db using psycopg2.
    Libraries:
        psycopg2.
    Other functions:
        None.
    Args:
        An "sql" query, an optional "query_variable", and a "db_connection".
    Returns:
        Query results as a list of tuples.
    Raises:
        None.
    """

    cursor = db_connection.cursor()
    if query_variable == 'no_query':           # If SQL query lacks a variable.
        cursor.execute(sql)
    else:
        cursor.execute(sql, query_variable)    # If SQL query has a variable.
    records = cursor.fetchall()
    cursor.close()

    return records
