"""
.. module:: get_or_create
   :synopsis: A module to obtain a current Chado table entry or create a new one.

.. moduleauthor:: Christopher Tabone ctabone@morgan.harvard.edu
"""

from sqlalchemy import (
    inspect,
    func)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session

import logging
log = logging.getLogger(__name__)


def get_or_create(session: Session, model, **kwargs):
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
        log.debug('Found rank column in {}'.format(model.__tablename__))
        # Get our unique constraints. We need to query with *only* these in order to get the correct rank value.
        unique_constraints = insp.get_unique_constraints(model.__tablename__)
        unique_constraints_list = unique_constraints[0]['column_names']
        log.debug('Unique constraints are {}'.format(unique_constraints))

        # Perform our query with only filters found as unique_constraints (minus rank).
        max_rank_kwargs = {k: kwargs[k] for k in unique_constraints_list if k != 'rank'}

        max_rank = session.query(func.max(model.rank)).\
            filter_by(**max_rank_kwargs).\
            one()

        if max_rank[0] is None:
            new_rank = {'rank': 0}
            log.debug('Rank value not found for current query, starting new rank at 0.')
            kwargs.update(new_rank)
            created = model(**kwargs)
        else:
            log.debug('Previous rank value exists when querying for unique constraints.')
            log.debug('Checking whether all values in this query currently exist.')
            try:
                attempt = session.query(model).filter_by(**kwargs).one()
                log.debug('Found previous entry for {}, insert not required.'.format(kwargs))
                return attempt, False
            except NoResultFound:
                log.debug('Max rank value for existing values is {}, incrementing to {} for current query.'
                          .format(max_rank[0], max_rank[0]+1))
                new_rank = {'rank': max_rank[0] + 1}
            kwargs.update(new_rank)
            created = model(**kwargs)
    else:
        try:
            attempt = session.query(model).filter_by(**kwargs).one()
            log.debug('Found previous entry for %s, insert not required.' % (kwargs))
            return attempt, False
        except NoResultFound:
            log.debug('Previous entry for %s not found. Adding insert.' % (kwargs))
            created = model(**kwargs)
    # Add the change and flush (no commits, leave that for the main program.)
    session.add(created)
    session.flush()

    return created, True
