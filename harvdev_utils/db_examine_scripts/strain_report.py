"""Strain Report.

Code to display all strain data and relationships etc for a given strain.

Can be used as the basis for future proforma work.

i.e. python strain_report.py -c chado.cfg -f SIP_S1_8 -l 2



* => added

  public | strain                                                          | table    | go
  public | strain_cvterm                                                   | table    | go
  public | strain_cvtermprop                                               | table    | go
  public | strain_dbxref                                                   | table    | go
  public | strain_feature                                                  | table    | go
  public | strain_featureprop                                              | table    | go
  public | strain_phenotype                                                | table    | go
  public | strain_phenotypeprop                                            | table    | go
  public | strain_pub                                                      | table    | go
  public | strain_relationship                                             | table    | go
  public | strain_relationship_pub                                         | table    | go
  public | strain_synonym                                                  | table    | go
  public | strainprop                                                      | table    | go
  public | strainprop_pub
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

from harvdev_utils.production import (Strain, StrainCvterm, StrainCvtermprop,
                                      StrainDbxref, StrainFeature,
                                      StrainFeatureprop, StrainPhenotype,
                                      StrainPhenotypeprop, Strainprop,
                                      StrainpropPub, StrainPub,
                                      StrainRelationship,
                                      StrainRelationshipPub, StrainSynonym)

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--strain', help=' (strain symbol to make report for)', required=True)
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


def get_strain(session, symbol, lookup_by):
    """Lookup strain."""
    log.info("Looking up strain '{}' using method '{}'".format(symbol, lookup_by))
    try:
        if lookup_by == 'name':
            return session.query(Strain).filter(Strain.name == symbol).one()
        elif lookup_by == 'uniquename':
            return session.query(Strain).filter(Strain.uniquename == symbol).one()
    except NoResultFound:
        log.info("Could NOT find '{}' by {}. exiting".format(symbol, lookup_by))
        exit(-1)
    except MultipleResultsFound:
        log.info("Could NOT find UNIQUE entry for '{}' by {}. exiting".format(symbol, lookup_by))
        exit(-1)


def report_strain(session, symbol, debug, limit, lookup_by):
    """Write report."""
    ###########################
    # starting point for report
    ###########################
    strain = get_strain(session, symbol, lookup_by)

    log.info("###################### Strain ############################")
    log.info(strain)
    log.info("###########################################################")
    # log.info(dir(feature))

    log.info("\n################### StrainPub #####################")
    fps = session.query(StrainPub).filter(StrainPub.strain_id == strain.strain_id)
    count = 0
    for fp in fps:
        count += 1
        if not limit or count <= limit:
            log.info(fp)

    log.info("\n################### Strainprop #####################")
    sps = session.query(Strainprop).filter(Strainprop.strain_id == strain.strain_id)
    count = 0
    for sp in sps:
        count += 1
        spps = session.query(StrainpropPub).filter(StrainpropPub.strainprop_id == sp.strainprop_id)
        for spp in spps:
            if not limit or count <= limit:
                log.info("StrainpropPub id={}: Strainprop id={} pub:{}".format(spp.strainprop_pub_id, sp.strainprop_id, spp.pub))
        log.info(sp)

    log.info("\n################### Synonyms ##############################")
    fss = session.query(StrainSynonym).filter(StrainSynonym.strain_id == strain.strain_id)
    count = 0
    for fs in fss:
        count += 1
        if not limit or count <= limit:
            log.info(fs)

    log.info("\n############# Features ##################")
    sfs = session.query(StrainFeature).filter(StrainFeature.strain_id == strain.strain_id)
    count = 0
    for sf in sfs:
        count += 1
        sfps = session.query(StrainFeatureprop).filter(StrainFeatureprop.strain_feature_id == sf.strain_feature_id)
        for sfp in sfps:
            if not limit or count <= limit:
                log.info("StrainFeatureprop id={}: rank={} value='{}' type=({})".format(sfp.strain_featureprop_id, sfp.rank, sfp.value, sfp.type))
        if not limit or count <= limit:
            log.info(sf)

    log.info("\n############# Subject Relationships ##################")
    srs = session.query(StrainRelationship).filter(StrainRelationship.subject_id == strain.strain_id)
    count = 0
    for sr in srs:
        count += 1
        srps = session.query(StrainRelationshipPub).filter(StrainRelationshipPub.strain_relationship_id == sr.strain_relationship_id)
        for srp in srps:
            if not limit or count <= limit:
                log.info("StrainRelationshipPub id={}: StrainRelationship_id = {}, pub:({})".format(srp.strain_relationship_pub_id, srp.strain_relationship_id, srp.pub))
        if not limit or count <= limit:
            log.info(sr)

    log.info("############# Object Relationships ##################")
    srs = session.query(StrainRelationship).filter(StrainRelationship.object_id == strain.strain_id)
    count = 0
    for sr in srs:
        count += 1
        srps = session.query(StrainRelationshipPub).filter(StrainRelationshipPub.strain_relationship_id == sr.strain_relationship_id)
        for srp in srps:
            if not limit or count <= limit:
                log.info("StrainRelationshipPub id={}: StrainRelationship_id = {}, pub:({})".format(srp.strain_relationship_pub_id, srp.strain_realationship_id, srp.pub))
        if not limit or count <= limit:
            log.info(sr)

    log.info("############# StrainCvtermxxxx ############")
    scs = session.query(StrainCvterm).filter(StrainCvterm.strain_id == strain.strain_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            scps = session.query(StrainCvtermprop).filter(StrainCvtermprop.strain_cvterm_id == sc.strain_cvterm_id)
            for scp in scps:
                log.info("StrainCvtermprop id={} StrainCvterm id={}: rank={} value='{}' type=({})".format(scp.strain_cvtermprop_id, sc.strain_cvterm_id, scp.rank, scp.value, scp.type))
            log.info(sc)

    log.info("############# StrainPhenotypexxxx ############")
    fcs = session.query(StrainPhenotype).filter(StrainPhenotype.strain_id == strain.strain_id)
    count = 0
    for fc in fcs:
        count += 1
        if not limit or count <= limit:
            fcds = session.query(StrainPhenotypeprop).filter(StrainPhenotypeprop.strain_phenotype_id == fc.strain_phenotype_id)
            for fcd in fcds:
                log.info("StrainPhenotypeprop id={}: StrainPhenotype id={}: rank={} value='{}' type={}".format(fcd.strain_phenotypeprop_id, fc.strain_phenotype_id, fcd.rank, fcd.value, fcd.type))
            log.info(fc)

    log.info("############ StrainDbxref #############")
    fds = session.query(StrainDbxref).filter(StrainDbxref.strain_id == strain.strain_id)
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)


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
    report_strain(session, args.strain, args.debug, args.limit, args.by)
