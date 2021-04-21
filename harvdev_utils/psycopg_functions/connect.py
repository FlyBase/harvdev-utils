"""Module:: connect.

Synopsis:
    Queries a postgres db by a psycopg2 connection.

Author(s):
    Chris Tabone ctabone@morgan.harvard.edu

"""


def connect(sql, query_variable, db_connection):
    """Retrieve information from a postgres db using psycopg2.

    Args:
        arg1 (string): An "sql" query.
        arg2 (tuple): An optional "query_variable": e.g., ('wingless', )
        arg3 (psycopg2.extensions.connection): A psycopg2 db connection.

    Returns:
        list: Query results as a list of tuples.

    """
    cursor = db_connection.cursor()
    if query_variable == 'no_query':           # If SQL query lacks a variable.
        cursor.execute(sql)
    else:
        cursor.execute(sql, query_variable)    # If SQL query has a variable.
    records = cursor.fetchall()
    cursor.close()

    return records
