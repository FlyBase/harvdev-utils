"""Test chado object string output."""
import argparse
import configparser
import logging
import sys
# Minimal prototype test for new proforma parsing software.
# SQL Alchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from production import (
    Analysisfeature, 
    CellLineCvtermprop, CellLineFeature, CellLineLibraryprop,
    CellLinePub, CellLineRelationship, CellLineStrain, CellLineSynonym,
    CellLinepropPub, CvtermDbxref, CvtermRelationship, Dbxrefprop,
    ExpressionCvtermprop, ExpressionPub, Expressionprop,
    Feature, Featureprop, Pub, FeaturePub, Organism,
    FeatureSynonym, Synonym
)


# from hardev_proforma_parser.src.chado_object.utils.feature_synonym import fs_add_by_synonym_name_and_type
# from src.chado_object.utils.feature import (
#      feature_symbol_lookup
# )
# from chado_object.utils.synonym import synonym_name_details

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', help='dump out all debug messages', default=False, action='store_true')
parser.add_argument('-c', '--config', help='Specify the location of the configuration file.', required=True)
args = parser.parse_args()

log = logging.getLogger(__name__)

# Import secure config variables.
config = configparser.ConfigParser()
config.read(args.config)

if args.debug:
    print("Running in Debug mode")
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(levelname)s -- %(message)s')
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    # comment/uncomment out below to notsee/see NOTICE messages for sql functions.
    # logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s -- %(message)s')


def create_postgres_session():
    """Connect to database."""
    USER = config['connection']['USER']
    PASSWORD = config['connection']['PASSWORD']
    SERVER = config['connection']['SERVER']

    DB = config['connection']['DB']

    log.info('Using server: {}'.format(SERVER))
    log.info('Using database: {}'.format(DB))

    # Create our SQL Alchemy engine from our environmental variables.
    engine_var = 'postgresql://' + USER + ":" + PASSWORD + '@' + SERVER + '/' + DB
    engine = create_engine(engine_var)

    Session = sessionmaker(bind=engine)
    session = Session()

    return session


def test_output(session):
    """Main test scripts."""
    # analysisfeature
    af = session.query(Analysisfeature).first()
    log.info(af)

    # Cell line only need to rpint the lowest level.
    # higher up levels get called internally.
    log.info('#####################################')
    clvp = session.query(CellLineCvtermprop).first()
    log.info(clvp)
    log.info('#####################################')
    clf = session.query(CellLineFeature).first()
    log.info(clf)
    log.info('#####################################')
    cllp = session.query(CellLineLibraryprop).first()
    log.info(cllp)
    log.info('#####################################')
    clp = session.query(CellLinePub).first()
    log.info(clp)
    log.info('#####################################')
    clr = session.query(CellLineRelationship).first()
    log.info(clr)
    log.info('#####################################')
    clsp = session.query(CellLineStrain).first()
    log.info(clsp)
    log.info('#####################################')
    clss = session.query(CellLineSynonym).first()
    log.info(clss)
    log.info('#####################################')
    clpp = session.query(CellLinepropPub).first()
    log.info(clpp)
    log.info('#####################################')

    # cvterms
    cd = session.query(CvtermDbxref).first()
    log.info(cd)
    log.info('#####################################')
    cr = session.query(CvtermRelationship).first()
    log.info(cr)
    log.info('#####################################')

    # dbxref
    dp = session.query(Dbxrefprop).first()
    log.info(dp)
    log.info('#####################################')

    # expression
    ecp = session.query(ExpressionCvtermprop).first()
    log.info(ecp)
    log.info('#####################################')
    ecp = session.query(ExpressionPub).first()
    log.info(ecp)
    log.info('#####################################')
    ecp = session.query(Expressionprop).first()
    log.info(ecp)
    log.info('#####################################')

if __name__ == '__main__':
    session = create_postgres_session()
    test_output(session)
