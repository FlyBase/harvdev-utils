"""
.. module:: get_or_create
   :synopsis: A module to obtain a current Chado table entry or create a new one.

.. moduleauthor:: Christopher Tabone ctabone@morgan.harvard.edu
"""

from sqlalchemy import (
    inspect,
    func)
from sqlalchemy.orm.exc import NoResultFound
import logging
import sys

log = logging.getLogger(__name__)


def get_create_or_update(session, model, **kwargs):
    """
    :param session: The current session in use by SQL Alchemy
    :param model: The table to be queried.
    :param kwargs: Values for the table used for lookup (e.g. name='awesome gene')
    :return: Both an SQL Alchemy object and True (if new object created) or False (if object retrieved)
    """

    # If rank exists in a table, we always insert our entry and increment the rank.
    log.debug('Submitted table: {}'.format(model.__tablename__))
    log.debug('Submitted kwargs: {}'.format(kwargs))
    # We need to get our engine back from our session to create an inspector.
    engine = session.get_bind()
    insp = inspect(engine)  # Used for inspecting the schema when needed.

    if 'rank' in model.__table__.columns:
        log.critical('Rank column found in {}.'.format(model.__tablename__))
        log.critical('This function does not work for tables with rank.')
        sys.exit(-1)



    try:
        attempt = session.query(model).filter_by(**kwargs).one()
        log.debug('Found previous entry for %s, create or update not required.' % (kwargs))
        return attempt, False
    except NoResultFound:
        log.debug('Previous entry for %s not found. Checking unique constraint query.' % (kwargs))

        # Perform our query with only filters found as unique_constraints.
        unique_constraints = insp.get_unique_constraints(model.__tablename__)
        unique_constraints_list = unique_constraints[0]['column_names']

        constraint_kwargs = {k: kwargs[k] for k in unique_constraints_list if k in kwargs}
        log.debug('Model unique constraints are {}'.format(unique_constraints))
        log.debug('New constraint kwargs for query are {}'.format(constraint_kwargs))

        query_result = session.query(model).filter_by(**constraint_kwargs).one_or_none()
        if not query_result:
            # If we find nothing, create a new entry with our arguments.
            created = model(**kwargs)
        else:
            # If we find an entry via unique constraints, update that entry.
            created = session.query(model).update(**kwargs)

        # Add the change and flush (no commits, leave that for the main program.)
        session.add(created)
        session.flush()

        return created, True
