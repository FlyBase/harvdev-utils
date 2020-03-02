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
    Feature, Featureprop, FeatureCvtermDbxref, FeatureCvtermprop,
    FeatureExpressionprop, FeatureGenotype, FeatureGrpmemberPub,
    FeatureHumanhealthDbxref, FeatureInteractionPub, FeatureInteractionprop,
    FeaturePhenotype, FeaturePubprop, FeatureRelationshipPub, FeatureRelationshippropPub,
    FeatureSynonym, FeaturelocPub, Featuremap, FeaturepropPub,
    GrpCvterm, GrpDbxref, GrpPub, GrpRelationshipPub, GrpRelationshipprop,
    GrpmemberCvterm, GrpmemberPub, Grpmemberprop, GrppropPub,
    HumanhealthCvtermprop, HumanhealthDbxrefpropPub, HumanhealthFeatureprop,
    HumanhealthPubprop, HumanhealthRelationshipPub, HumanhealthSynonym,
    HumanhealthpropPub
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
    clpp = session.query(CellLineLibraryprop).first()
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

    # feature
    f = session.query(Feature).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureSynonym).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(Featureprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureCvtermprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureCvtermDbxref).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureExpressionprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureGenotype).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureGrpmemberPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureHumanhealthDbxref).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureInteractionPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureInteractionprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeaturePhenotype).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeaturePubprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureRelationshipPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureRelationshippropPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeatureSynonym).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeaturelocPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(Featuremap).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(FeaturepropPub).first()
    log.info(f)
    log.info('#####################################')

    # grp
    f = session.query(GrpCvterm).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(GrpDbxref).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(GrpPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(GrpRelationshipPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(GrpRelationshipprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(GrpmemberCvterm).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(GrpmemberPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(Grpmemberprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(GrppropPub).first()
    log.info(f)
    log.info('#####################################')

    # HH
    f = session.query(HumanhealthCvtermprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(HumanhealthDbxrefpropPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(HumanhealthFeatureprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(HumanhealthPubprop).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(HumanhealthRelationshipPub).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(HumanhealthSynonym).first()
    log.info(f)
    log.info('#####################################')
    f = session.query(HumanhealthpropPub).first()
    log.info(f)
    log.info('#####################################')


if __name__ == '__main__':
    session = create_postgres_session()
    test_output(session)
