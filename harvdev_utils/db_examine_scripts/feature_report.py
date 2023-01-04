"""Feature Report."""
import argparse
import configparser
import logging
import sys
import os

# Minimal prototype test for new proforma parsing software.
# SQL Alchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from harvdev_utils.chado_functions import (feature_name_lookup,
                                           feature_symbol_lookup,
                                           get_feature_by_uniquename)
from harvdev_utils.production import (Cvterm, FeatureCvterm, FeatureCvtermDbxref,
                                      FeatureCvtermprop, FeatureDbxref,
                                      FeatureExpression, FeatureGenotype,
                                      FeatureGrpmember,
                                      FeatureHumanhealthDbxref,
                                      FeatureInteraction, Featureloc, FeaturePhenotype,
                                      Featureprop, FeaturepropPub, FeaturePub,
                                      FeatureRelationship, FeatureRelationshipPub,
                                      FeatureRelationshipprop, FeatureRelationshippropPub,
                                      FeatureSynonym, HumanhealthFeature, Phendesc,
                                      LibraryFeature, LibraryFeatureprop,
                                      Phenstatement, Pub)

description = """
Code to display all feature data and relationships etc for a given feature.

Can be used as the basis for future proforma work.

"""

examples = """

Dref-XR has feature expressions.
i.e. python feature_report.py -c chado.cfg -f Dref-XR -l 2 -t RNA

Bre1 has feature grpmember
python feature_report.py -c chado.cfg -f Bre1 -l 2

feature interaction:-
python feature_report.py -c chado.cfg -f 'Ppat-Dpck-XP' -l 2 -t protein

test db:-
python3 feature_report.py -f symbol-41 -b symbol -c tester.cfg

"""
parser = argparse.ArgumentParser(description=description, epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-f', '--featuresymbol', help=' (feature symbol to make report for)', required=True)
parser.add_argument('-t', '--type', help=' (feature type to make report for)', required=False)
parser.add_argument('-b', '--by', help='lookup by', choices=['symbol', 'name', 'uniquename'], default='symbol')
parser.add_argument('-d', '--debug', help='dump out all debug messages', default=False, action='store_true')
parser.add_argument('-c', '--config', help='Specify the location of the configuration file.', required=True)
parser.add_argument('-o', '--obsolete', help='Specify if feature is obsolete.', default=False, action='store_true')
parser.add_argument('-l', '--limit', help='Limit to x for each table', type=int, default=0, required=False)
args = parser.parse_args()

log = logging.getLogger(__name__)

if args.debug:
    print("Running in Debug mode")
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(levelname)s -- %(message)s')
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    # comment/uncomment out below to notsee/see NOTICE messages for sql functions.
    # logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s -- %(message)s')

if args.obsolete:
    obsolete = 't'
else:
    obsolete = 'f'

# Import secure config variables.
config = configparser.ConfigParser()
config.read(args.config)
if 'connection' not in config:
    cfg_file = args.config  # try with .cfg at the end if missed.
    log.debug("Unable to load valid file {}.".format(cfg_file))
    if ".cfg" not in cfg_file:
        cfg_file += ".cfg"
    config.read(cfg_file)
    full_file = ''
    if 'connection' not in config and cfg_file.startswith("."):
        print("Unable to find config file.")
        exit(-1)
    if 'connection' not in config:  # lets try where this program is.
        log.debug("Unable to load valid file {} either.".format(cfg_file))
        wd = os.path.dirname(os.path.realpath(__file__))
        full_file = os.path.join(wd, cfg_file)
        config.read(full_file)
    if 'connection' not in config:  # Finally lets try in /data...
        log.debug("Failed to load valid {} file.".format(full_file))
        full_file = '/data/credentials/proforma/{}'.format(cfg_file)
        config.read(full_file)
    if 'connection' not in config:
        print("Unable to find config file anywhere.")
        exit(-1)


def get_feature(session, feature_symbol, feature_type, lookup_by, obsolete):
    """Lookup feature."""
    log.info("Looking up feature '{}' of type '{}' using method '{}' an obsolete='{}'".format(feature_symbol, feature_type, lookup_by, obsolete))
    try:
        if lookup_by == 'symbol':
            return feature_symbol_lookup(session, feature_type, feature_symbol, obsolete=obsolete)
        elif lookup_by == 'name':
            return feature_name_lookup(session, feature_symbol, type_name=feature_type, obsolete=obsolete)
        elif lookup_by == 'uniquename':
            return get_feature_by_uniquename(session, feature_symbol, feature_type, obsolete=obsolete)
    except NoResultFound:
        log.info("Could NOT find '{}' of type '{}'. exiting".format(feature_symbol, feature_type))
        exit(-1)
    except MultipleResultsFound:
        log.info("Could NOT find UNIQUE entry for '{}' of type '{}'. exiting".format(feature_symbol, feature_type))
        if lookup_by == 'symbol':
            features = feature_symbol_lookup(session, feature_type, feature_symbol, check_unique=False, obsolete=obsolete)
            for feature in features:
                print("{}".format(feature))
        exit(-1)


def report(session, feature_symbol, feature_type, debug, limit, lookup_by, obsolete):
    """Write report."""
    ###########################
    # starting point for report
    ###########################
    feature = get_feature(session, feature_symbol, feature_type, lookup_by, obsolete)

    log.info("###################### Feature ############################")
    log.info(feature)
    log.info("###########################################################")
    # log.info(dir(feature))

    if not feature:
        print("Error: Feature not found")
        exit(-1)

    log.info("\n################### FeaturePub #####################")
    fps = session.query(FeaturePub).filter(FeaturePub.feature_id == feature.feature_id)
    count = 0
    for fp in fps:
        count += 1
        if not limit or count <= limit:
            log.info(fp)

    log.info("\n################### Featureprop #####################")
    fps = session.query(Featureprop).filter(Featureprop.feature_id == feature.feature_id)
    count = 0
    for fp in fps:
        count += 1
        fpps = session.query(FeaturepropPub).filter(FeaturepropPub.featureprop_id == fp.featureprop_id)
        for fpp in fpps:
            if not limit or count <= limit:
                message = "FeaturepropPub id={}, Featureprop id={}:\n\tPub:({})".\
                    format(fpp.featureprop_pub_id, fp.featureprop_id, fpp.pub)
                log.info(message)
        if not limit or count <= limit:
            log.info(fp)

    log.info("################### Synonyms ##############################")
    fss = session.query(FeatureSynonym).filter(FeatureSynonym.feature_id == feature.feature_id)
    count = 0
    for fs in fss:
        count += 1
        if not limit or count <= limit:
            log.info(fs)

    log.info("############# Object Relationships ##################")
    frs = session.query(FeatureRelationship).filter(FeatureRelationship.object_id == feature.feature_id)

    count = 0
    for fr in frs:
        message = f"{fr}"
        frpubs = session.query(FeatureRelationshipPub).\
            filter(FeatureRelationshipPub.feature_relationship_id == fr.feature_relationship_id)
        pubs = []
        for frpub in frpubs:
            # log.debug(f"{frpub}")
            pub = session.query(Pub).filter(Pub.pub_id == frpub.pub_id).one()
            pubs.append(f"{pub.uniquename}")
            # log.info(f"\n\t{pub}\n")
        message += f"\n\tPubs: {pubs}"
        frps = session.query(FeatureRelationshipprop).\
            filter(FeatureRelationshipprop.feature_relationship_id == fr.feature_relationship_id).all()

        for frp in frps:
            cvterm = session.query(Cvterm).\
                filter(Cvterm.cvterm_id == frp.type_id).one()
            message += f"\n\tFeatureRelationshipProp rank={frp.rank} value={frp.value} cvterm='{cvterm.name}' cv='{cvterm.cv.name}' "
            pubs = []
            frpps = session.query(FeatureRelationshippropPub).\
                filter(FeatureRelationshippropPub.feature_relationshipprop_id == frp.feature_relationshipprop_id).all()
            for frpp in frpps:
                pubs.append(f"{frpp.pub.uniquename}")
            message += f"{pubs}"
        log.info(message)

    log.info("############# Subject Relationships ##################")
    frs = session.query(FeatureRelationship).filter(FeatureRelationship.subject_id == feature.feature_id)

    count = 0
    for fr in frs:
        message = f"{fr}"
        frpubs = session.query(FeatureRelationshipPub).\
            filter(FeatureRelationshipPub.feature_relationship_id == fr.feature_relationship_id)
        pubs = []
        for frpub in frpubs:
            # log.debug(f"{frpub}")
            pub = session.query(Pub).filter(Pub.pub_id == frpub.pub_id).one()
            pubs.append(f"{pub.uniquename}")
            # log.info(f"\n\t{pub}\n")
        message += f"\n\tPubs: {pubs}"
        frps = session.query(FeatureRelationshipprop).\
            filter(FeatureRelationshipprop.feature_relationship_id == fr.feature_relationship_id).all()

        for frp in frps:
            cvterm = session.query(Cvterm).\
                filter(Cvterm.cvterm_id == frp.type_id).one()
            message += f"\n\tFeatureRelationshipProp rank={frp.rank} value={frp.value} cvterm='{cvterm.name}' cv='{cvterm.cv.name}' "
            pubs = []
            frpps = session.query(FeatureRelationshippropPub).\
                filter(FeatureRelationshippropPub.feature_relationshipprop_id == frp.feature_relationshipprop_id).all()
            for frpp in frpps:
                pubs.append(f"{frpp.pub.uniquename}")
            message += f"{pubs}"
        log.info(message)

    log.info("############# HumanhealthFeature #######")
    fhds = session.query(HumanhealthFeature).filter(HumanhealthFeature.feature_id == feature.feature_id)
    count = 0
    for fhd in fhds:
        count += 1
        if not limit or count <= limit:
            log.info(fhd)

    log.info("############# FeatureHumanhealthDbxref #######")
    fhds = session.query(FeatureHumanhealthDbxref).filter(FeatureHumanhealthDbxref.feature_id == feature.feature_id)
    count = 0
    for fhd in fhds:
        count += 1
        if not limit or count <= limit:
            log.info(fhd)

    log.info("############# FeatureCvtermxxxx ############")
    fcs = session.query(FeatureCvterm).filter(FeatureCvterm.feature_id == feature.feature_id)
    count = 0
    for fc in fcs:
        count += 1
        seen = False
        if not limit or count <= limit:
            # log.info(fc)
            # none of the following
            fcds = session.query(FeatureCvtermDbxref).filter(FeatureCvtermDbxref.feature_cvterm_id == fc.feature_cvterm_id)
            for fcd in fcds:
                seen = True
                log.info(fcd)
            # It has these though
            fcds = session.query(FeatureCvtermprop).filter(FeatureCvtermprop.feature_cvterm_id == fc.feature_cvterm_id)
            for fcd in fcds:
                seen = True
                log.info(fcd)
            if not seen:
                log.info(fc)
    log.info("############ FeatureDbxref #############")
    fds = session.query(FeatureDbxref).filter(FeatureDbxref.feature_id == feature.feature_id)
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("############ FeatureExpression #############")
    fds = session.query(FeatureExpression).filter(FeatureExpression.feature_id == feature.feature_id).all()
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("############ FeatureGenotype #############")
    fgs = session.query(FeatureGenotype).filter(FeatureGenotype.feature_id == feature.feature_id).all()
    count = 0
    for fg in fgs:
        log.info(fg)
        count += 1
        if not limit or count <= limit:
            pss = session.query(Phenstatement).filter(Phenstatement.genotype_id == fg.genotype_id).all()
            if pss:
                for ps in pss:
                    log.info(ps)
            pss = session.query(Phendesc).filter(Phendesc.genotype_id == fg.genotype_id).all()
            if pss:
                for ps in pss:
                    log.info(ps)

    log.info("############ FeaturePhenotype #############")
    fds = session.query(FeaturePhenotype).filter(FeaturePhenotype.feature_id == feature.feature_id)
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("############ FeatureGrpMember #############")
    fds = session.query(FeatureGrpmember).filter(FeatureGrpmember.feature_id == feature.feature_id)
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("############ FeatureInteraction #############")
    fis = session.query(FeatureInteraction).filter(FeatureInteraction.feature_id == feature.feature_id)
    count = 0
    for fd in fis:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("############ Featureloc #############")
    fis = session.query(Featureloc).filter(Featureloc.feature_id == feature.feature_id)
    count = 0
    for fd in fis:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("########### LibraryFeature ###########")
    lfs = session.query(LibraryFeature).filter(LibraryFeature.feature_id == feature.feature_id)
    count = 0
    for lf in lfs:
        seen = False
        if not limit or count <= limit:
            # log.info(fc)
            # none of the following
            lfps = session.query(LibraryFeatureprop).filter(LibraryFeatureprop.library_feature_id == lf.library_feature_id)
            for lfp in lfps:
                seen = True
                log.info(lfp)
        if not seen:
            log.info(lf)


def create_postgres_session():
    """Connect to database."""
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


if __name__ == '__main__':
    session = create_postgres_session()
    report(session, args.featuresymbol, args.type, args.debug, args.limit, args.by, obsolete)
