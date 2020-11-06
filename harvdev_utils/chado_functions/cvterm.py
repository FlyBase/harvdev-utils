# store easy lookup for cv, cvterm lookups
# Also cvterm methids are here.
# should save time in the long run
from sqlalchemy.orm.exc import NoResultFound
# from sets import Set

from .chado_errors import CodingError
from harvdev_utils.production import (
    Cv, Cvterm, Cvtermprop, Db, Dbxref
)

# Caches
cv_cvterm = {}
cvterm_id_to_props = {}         # i.e. 123 => ['clone_qualifier', 'envoronment_qualifier']
db_propname_to_cvterm_ids = {}  # i.e  FBcv:environment => Set cvterm_ids i.e. [123, 124]
retained = {}                   # Special name to all cvterm_id's for that as a Set


def get_cvterm(session, cv_name, cvterm_name):
    """Lookup cvterm."""
    global cv_cvterm
    try:
        return cv_cvterm[cv_name][cvterm_name]
    except KeyError:
        pass
    try:
        cvterm = session.query(Cvterm).join(Cv).\
            filter(Cvterm.name == cvterm_name,
                   Cv.name == cv_name,
                   Cvterm.is_obsolete == 0).one()
        if cv_name not in cv_cvterm:
            cv_cvterm[cv_name] = {}
        cv_cvterm[cv_name][cvterm_name] = cvterm
    except NoResultFound:
        raise CodingError("HarvdevError: Could not find cv {}, cvterm {}.".format(cv_name, cvterm_name))
        return None
    return cv_cvterm[cv_name][cvterm_name]

########################
# cvterm props functions
########################


def check_cvterm_has_prop(session, cvterm, prop_value):
    """Check cvterm has a specific prop value.

    cvterm: (Cvterm Object) - Cvterm object.
    prop_value:  (str) - Value fo cvterm prop.

    Return True or False depending on wether it was found or not.
    """
    global cvterm_id_to_props
    found = False
    cvterm_id = cvterm.cvterm_id
    if cvterm.cvterm_id in cvterm_id_to_props:
        if prop_value in cvterm_id_to_props[cvterm_id]:
            found = True
        return found

    # look up cvtermprops for this cvterm
    props = session.query(Cvtermprop).filter(Cvtermprop.cvterm_id == cvterm_id).all()
    cvterm_id_to_props[cvterm_id] = set()
    for prop in props:
        cvterm_id_to_props[cvterm_id].add(prop.value)
    return prop_value in cvterm_id_to_props[cvterm_id]


def check_cvterm_is_allowed(session, cvterm, list_of_props, retain_name=None):
    """Check if cvterm is allowed.

    cvterm: (Cvterm Object) - Cvterm object.
    list_of_props: (list) list of db:propnames to lookup
        i.e. ['FBdv:default', 'FBcv:environment_qualifier']
    retain_name: <optional> (str)
        If set will create and keep list of cvterms allowed and store this in retained.
        NOTE: Will suck up memory depending on number BUT
            will allow faster lookup later on if we anticipate
            this being used a lot.
        If not set it will create a name by joining list element into a str.
    """
    global db_propname_to_cvterm_ids, retained

    # create retained values for list of props
    if not retain_name:
        retain_name = '-'.join(list_of_props)
    if retain_name in retained:
        if cvterm.cvterm_id in retained[retain_name]:
            return True
        return False
    else:
        retained[retain_name] = set()

    for db_and_propname in list_of_props:
        if db_and_propname in db_propname_to_cvterm_ids:
            retained[retain_name].extend(db_propname_to_cvterm_ids[db_and_propname])
            continue
        db_name, prop_name = db_and_propname.split(':')
        if not prop_name:
            print("AHHHHHH {} failed to be split. Need to raise excpetion etc".format(db_and_propname))
            pass  # some sort of exception raise here.
        filter_spec = (Db.name == db_name,)
        # filter_spec = ()
        if prop_name != 'default':
            filter_spec += (Cvtermprop.value == prop_name,)

        cvterms = session.query(Cvterm).\
            join(Cvtermprop, Cvterm.cvterm_id == Cvtermprop.cvterm_id).\
            join(Dbxref, Cvterm.dbxref_id == Dbxref.dbxref_id).join(Db).\
            filter(*filter_spec).all()
        db_propname_to_cvterm_ids[db_and_propname] = set()
        for item in cvterms:
            db_propname_to_cvterm_ids[db_and_propname].add(item.cvterm_id)
            print("adding {}".format(item))
        retained[retain_name].update(db_propname_to_cvterm_ids[db_and_propname])
    print(str(retained[retain_name]))
    if cvterm.cvterm_id in retained[retain_name]:
        return True
    return False
