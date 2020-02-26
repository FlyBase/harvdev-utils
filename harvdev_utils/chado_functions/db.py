# store easy lookup for db's
# should save time in the long run
from ..production import Db
from sqlalchemy.orm.exc import NoResultFound
from .chado_errors import CodingError
db_dict = {}


def get_db(session, db_name):
    """Lookup db chado object given name."""
    global db_dict
    try:
        return db_dict[db_name]
    except KeyError:
        pass
    try:
        db = session.query(Db).filter(Db.name == db_name).one()
        if db:
            db_dict[db_name] = db
    except NoResultFound:
        raise CodingError("HarvdevError: Could not find db {}.".format(db_name))
        return None
    return db_dict[db_name]
