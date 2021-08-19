"""Grp Report.

Code to display all grp data and relationships etc for a given grp.

Can be used as the basis for future proforma work.

i.e. python grp_report.py -c chado.cfg -f RAD50 -l 2



* => added

 public | grp                                                             | table    | go
 public | grp_cvterm                                                      | table    | go
 public | grp_dbxref                                                      | table    | go
 public | grp_pub                                                         | table    | go
 public | grp_pubprop                                                     | table    | go
 public | grp_relationship                                                | table    | go
 public | grp_relationship_pub                                            | table    | go
 public | grp_relationshipprop                                            | table    | go
 public | grp_synonym                                                     | table    | go
 public | grpmember                                                       | table    | go
 public | grpmember_cvterm                                                | table    | go
 public | grpmember_pub                                                   | table    | go
 public | grpmemberprop                                                   | table    | go
 public | grpmemberprop_pub                                               | table    | go
 public | grpprop                                                         | table    | go
 public | grpprop_pub                                                     | table    | go

 public | feature_grpmember                                               | table    | go
 public | feature_grpmember_pub                                           | table    | go

"""
import argparse
import configparser
import logging
import sys

# Minimal prototype test for new proforma parsing software.
# SQL Alchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from harvdev_utils.production import (Grp, GrpCvterm, GrpDbxref, Grpprop,
                                      GrppropPub, GrpPub,
                                      GrpRelationship, GrpRelationshipprop,
                                      GrpRelationshipPub, GrpSynonym)
from harvdev_utils.production.production import FeatureGrpmember, Grpmember

parser = argparse.ArgumentParser()
parser.add_argument('-g', '--grp', help=' (grp symbol to make report for)', required=True)
parser.add_argument('-b', '--by', help='lookup by', choices=['name', 'uniquename'], default='name')
parser.add_argument('-d', '--debug', help='dump out all debug messages', default=False, action='store_true')
parser.add_argument('-c', '--config', help='Specify the location of the configuration file.', required=True)
parser.add_argument('-l', '--limit', help='Limit to x for each table', type=int, default=0, required=False)
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


def get_grp(session, symbol, lookup_by):
    """Lookup grp."""
    log.info("Looking up grp '{}' using method '{}'".format(symbol, lookup_by))
    try:
        if lookup_by == 'name':
            return session.query(Grp).filter(Grp.name == symbol).one()
        elif lookup_by == 'uniquename':
            return session.query(Grp).filter(Grp.uniquename == symbol).one()
    except NoResultFound:
        log.info("Could NOT find '{}' by {}. exiting".format(symbol, lookup_by))
        exit(-1)
    except MultipleResultsFound:
        log.info("Could NOT find UNIQUE entry for '{}' by {}. exiting".format(symbol, lookup_by))
        exit(-1)


def report_grp(session, symbol, debug, limit, lookup_by):
    """Write report."""
    ###########################
    # starting point for report
    ###########################
    Grp = get_grp(session, symbol, lookup_by)

    log.info("###################### Grp ############################")
    log.info(Grp)
    log.info("###########################################################")
    # log.info(dir(feature))

    log.info("\n################### GrpPub #####################")
    fps = session.query(GrpPub).filter(GrpPub.grp_id == Grp.grp_id)
    count = 0
    for fp in fps:
        count += 1
        if not limit or count <= limit:
            log.info(fp)

    log.info("\n################### Grpprop #####################")
    sps = session.query(Grpprop).filter(Grpprop.grp_id == Grp.grp_id)
    count = 0
    for sp in sps:
        count += 1
        spps = session.query(GrppropPub).filter(GrppropPub.grpprop_id == sp.grpprop_id)
        for spp in spps:
            if not limit or count <= limit:
                log.info("GrppropPub id={}: Grpprop id={} pub:{}".format(spp.grpprop_pub_id, sp.grpprop_id, spp.pub))
        log.info(sp)

    log.info("\n################### Synonyms ##############################")
    fss = session.query(GrpSynonym).filter(GrpSynonym.grp_id == Grp.grp_id)
    count = 0
    for fs in fss:
        count += 1
        if not limit or count <= limit:
            log.info(fs)

    log.info("\n############# Subject Relationships ##################")
    srs = session.query(GrpRelationship).filter(GrpRelationship.subject_id == Grp.grp_id)
    count = 0
    for sr in srs:
        count += 1
        srps = session.query(GrpRelationshipPub).filter(GrpRelationshipPub.grp_relationship_id == sr.grp_relationship_id)
        for srp in srps:
            if not limit or count <= limit:
                log.info("GrpRelationshipPub id={}: GrpRelationship_id = {}, pub:({})".format(srp.grp_relationship_pub_id, srp.grp_relationship_id, srp.pub))
        srps = session.query(GrpRelationshipprop).filter(GrpRelationshipprop.grp_relationship_id == sr.grp_relationship_id)
        for srp in srps:
            if not limit or count <= limit:
                log.info("GrpRelationshipprop id={}: GrpRelationship_id = {}, pub:({})".format(srp.grp_relationship_pub_id, srp.grp_relationship_id, srp.pub))
        if not limit or count <= limit:
            log.info(sr)

    log.info("############# Object Relationships ##################")
    srs = session.query(GrpRelationship).filter(GrpRelationship.object_id == Grp.grp_id)
    count = 0
    for sr in srs:
        count += 1
        srps = session.query(GrpRelationshipPub).filter(GrpRelationshipPub.grp_relationship_id == sr.grp_relationship_id)
        for srp in srps:
            if not limit or count <= limit:
                log.info("GrpRelationshipPub id={}: GrpRelationship_id = {}, pub:({})".format(srp.grp_relationship_pub_id, srp.grp_realationship_id, srp.pub))
        if not limit or count <= limit:
            log.info(sr)

    log.info("############# GrpCvtermxxxx ############")
    scs = session.query(GrpCvterm).filter(GrpCvterm.grp_id == Grp.grp_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            log.info(sc)

    log.info("############ GrpDbxref #############")
    fds = session.query(GrpDbxref).filter(GrpDbxref.grp_id == Grp.grp_id)
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("######### members ##########")
    # select * from grpmember gm, feature_grpmember fgm, feature f where fgm.feature_id = f.feature_id and fgm.grpmember_id = gm.grpmember_id and grp_id = 1709;
    # grpmember_id | rank | type_id | grp_id | feature_grpmember_id | grpmember_id | feature_id | feature_id | dbxref_id | organism_id | name | uniquename  | residues | seqlen | md5checksum | type_id | is_analysis |      timeaccessioned       |      timelastmodified      | is_obsolete 
    # --------------+------+---------+--------+----------------------+--------------+------------+------------+-----------+-------------+------+-------------+----------+--------+-------------+---------+-------------+----------------------------+----------------------------+-------------
    #         1372 |    0 |  128600 |   1709 |                13794 |         1372 |    3093032 |    3093032 |     77929 |           1 | cpa  | FBgn0034577 |          |   2097 |             |     219 | f           | 2003-12-01 17:17:44.209359 | 2013-03-12 17:34:25.983929 | f
    #         1372 |    0 |  128600 |   1709 |                13795 |         1372 |    3130840 |    3130840 |    145227 |           1 | cpb  | FBgn0011570 |          |   2061 |             |     219 | f           | 2003-12-01 19:29:00.901133 | 2012-02-27 18:10:29.65761  | f
    # (2 rows)
    members = session.query(FeatureGrpmember).join(Grpmember).filter(Grpmember.grp_id == Grp.grp_id)
    for member in members:
        log.info(member)


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
    report_grp(session, args.grp, args.debug, args.limit, args.by)
