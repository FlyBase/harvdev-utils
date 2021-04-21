# store easy lookup for db's and dbxrefs
# should save time in the long run
from ..production import Db, Dbxref
from sqlalchemy.orm.exc import NoResultFound
from .chado_errors import CodingError, DataError
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


def get_dbxref(session, db_name, accession):
    """Lookup dbxref using db name and accession."""
    try:
        db = get_db(session, db_name)
    except CodingError:
        raise DataError("Could not find db {}.".format(db_name))
    try:
        dbxref = session.query(Dbxref).filter(Dbxref.db_id == db.db_id,
                                              Dbxref.accession == accession).one()
    except NoResultFound:
        raise DataError("DataError: Could not find dbxref for {} {}.".format(db_name, accession))
    return dbxref
