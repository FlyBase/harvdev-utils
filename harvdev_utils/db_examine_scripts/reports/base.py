"""
General object to help dump out data for a given object.
"""
import traceback
# import harvdev_utils.production as production
import configparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import logging
log = logging.getLogger(__name__)

# tuple indexes for table_info
CLASS_OBJECT = 0
RELATED_CLASS = 1


class BaseObject(object):
    """Base Object."""

    def __init__(self, params):
        """Initialise the object."""

        # table_info need to be set up for each child
        # i.e. [
        #      (CellLinePub, [{"related_class": CellLinePub, "related_id_name": 'cell_line_id'}]),
        #      (CellLineprop, [{"related_class": CellLinepropPub, "related_id_name": 'cell_line_prop_id'}])
        #      ]
        self.table_info = []
        self.session = self.create_postgres_session(params.get('config'))
        self.chado_object = None
        self.primary_key_name = None  # set up in child .ie. for CellLine it is cell_line_id

    def create_postgres_session(self, config_file):
        """Connect to database."""
        # Import secure config variables
        config = configparser.ConfigParser()
        log.debug("config_file is {}".format(config_file))
        config.read(config_file)
        log.debug("config is {}".format(config))
        USER = config['connection']['USER']
        PASSWORD = config['connection']['PASSWORD']
        SERVER = config['connection']['SERVER']
        try:
            PORT = config['connection']['PORT']
        except KeyError:
            PORT = '5432'

        DB = config['connection']['DB']

        log.info('Using server: {}'.format(SERVER))
        log.info('Using database: {}'.format(DB))

        # Create our SQL Alchemy engine from our environmental variables.
        engine_var = 'postgresql://' + USER + ":" + PASSWORD + '@' + SERVER + ':' + PORT + '/' + DB
        engine = create_engine(engine_var)

        Session = sessionmaker(bind=engine)
        session = Session()

        return session

    def get_object(self, symbol, lookup_by):
        """Lookup CellLine."""
        log.info("Looking up '{}' using method '{}'".format(symbol, lookup_by))

        try:
            if lookup_by == 'name':
                name_statement = getattr(self.chado_object, 'name')
                return self.session.query(self.chado_object).filter(name_statement == symbol).one()
            elif lookup_by == 'uniquename':
                uniquename_statement = getattr(self.chado_object, 'uniquename')
                return self.session.query(self.chado_object).filter(uniquename_statement == symbol).one()
        except NoResultFound:
            log.info("Could NOT find '{}' by {}. exiting".format(symbol, lookup_by))
            exit(-1)
        except MultipleResultsFound:
            log.info("Could NOT find UNIQUE entry for '{}' by {}. exiting".format(symbol, lookup_by))
            exit(-1)

    def dump_data(self):
        """Dump the data for this object."""
        log.info(self.chado_object)
        for item in self.table_info:
            log.debug("item {}".format(item))
            try:
                lookup_id_statement = getattr(item[CLASS_OBJECT], self.primary_key_name)
                # session.query(CellLineprop).filter(CellLineprop.cell_line_id == CellLine.cell_line_id)
                hits = self.session.query(item[CLASS_OBJECT]).filter(lookup_id_statement == self.chado_object.id())
                for obj in hits:
                    count = 0
                    try:
                        for related_dict in item[RELATED_CLASS]:
                            related_id_statement = getattr(related_dict["related_class"], related_dict["related_id_name"])
                            # session.query(CellLinepropPub).filter(CellLinepropPub.cell_lineprop_id == sp.cell_lineprop_id)
                            relateds = self.session.query(related_dict["related_class"]).filter(related_id_statement == obj.id())
                            for related in relateds:
                                count += 1
                                log.info(related)
                    except Exception as e:
                        log.error("Exception: {}".format(e))
                        traceback.print_tb(e.__traceback__)
                    if not count:  # it had no related tables or entries
                        log.info(obj)
            except Exception as e:
                log.error("Exception: {}".format(e))
                traceback.print_tb(e.__traceback__)
