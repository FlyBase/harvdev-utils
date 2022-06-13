"""Genotype Report.

Code to display all Genotype data and relationships etc for a given Genotype.

Can be used as the basis for future proforma work.

i.e. python Genotype_report.py -c chado.cfg -f SIP_S1_8 -l 2



* => added

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

from harvdev_utils.production import (Genotype, GenotypeCvterm, GenotypeCvtermprop,
                                      GenotypeDbxref, FeatureGenotype,
                                      Genotypeprop,
                                      GenotypepropPub, GenotypePub,
                                      GenotypeSynonym,
                                      Phendesc, PhenotypeComparison, Phenstatement)
from sqlalchemy.orm.session import Session

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--Genotype', help=' (Genotype symbol to make report for)', required=True)
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


def get_Genotype(session: Session, symbol: str, lookup_by: str) -> Genotype:
    """Lookup Genotype."""
    log.info("Looking up Genotype '{}' using method '{}'".format(symbol, lookup_by))
    try:
        if lookup_by == 'name':
            log.info("Ignoring lookup by name as only unique names are set.")
            return session.query(Genotype).filter(Genotype.uniquename == symbol).one()
        elif lookup_by == 'uniquename':
            return session.query(Genotype).filter(Genotype.uniquename == symbol).one()
    except NoResultFound:
        log.info("Could NOT find '{}' by uniquename. exiting".format(symbol))
        exit(-1)
    except MultipleResultsFound:
        log.info("Could NOT find UNIQUE entry for '{}' by uniquename. exiting".format(symbol))
        exit(-1)


def report_Genotype(session: Session, symbol: str, debug: bool, limit: int, lookup_by: str):  # noqa
    """Write report."""
    ###########################
    # starting point for report
    ###########################
    Genotype = get_Genotype(session, symbol, lookup_by)
    print("BOB: {} {}".format(type(Genotype), Genotype.__class__.__bases__))
    log.info("###################### Genotype ############################")
    log.info(Genotype)
    log.info("###########################################################")
    # log.info(dir(feature))

    log.info("\n################### GenotypePub #####################")
    fps = session.query(GenotypePub).filter(GenotypePub.genotype_id == Genotype.genotype_id)
    count = 0
    for fp in fps:
        count += 1
        if not limit or count <= limit:
            log.info(fp)

    log.info("\n################### Genotypeprop #####################")
    sps = session.query(Genotypeprop).filter(Genotypeprop.genotype_id == Genotype.genotype_id)
    count = 0
    for sp in sps:
        count += 1
        spps = session.query(GenotypepropPub).filter(GenotypepropPub.cell_lineprop_id == sp.cell_lineprop_id)
        for spp in spps:
            if not limit or count <= limit:
                log.info("GenotypepropPub id={}: Genotypeprop id={} pub:{}".format(spp.cell_lineprop_pub_id, sp.cell_lineprop_id, spp.pub))
        log.info(sp)

    log.info("\n################### Synonyms ##############################")
    fss = session.query(GenotypeSynonym).filter(GenotypeSynonym.genotype_id == Genotype.genotype_id)
    count = 0
    for fs in fss:
        count += 1
        if not limit or count <= limit:
            log.info(fs)

    log.info("\n############# Features ##################")
    sfs = session.query(FeatureGenotype).filter(FeatureGenotype.genotype_id == Genotype.genotype_id)
    count = 0
    for sf in sfs:
        count += 1
        if not limit or count <= limit:
            log.info(sf)

    log.info("############# GenotypeCvtermxxxx ############")
    scs = session.query(GenotypeCvterm).filter(GenotypeCvterm.genotype_id == Genotype.genotype_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            scps = session.query(GenotypeCvtermprop).filter(GenotypeCvtermprop.cell_line_cvterm_id == sc.cell_line_cvterm_id)
            for scp in scps:
                mess = "GenotypeCvtermprop id={} GenotypeCvterm id={}: rank={} value='{}' type=({})".\
                    format(scp.cell_line_cvtermprop_id, sc.cell_line_cvterm_id, scp.rank, scp.value, scp.type)
                log.info(mess)
            log.info(sc)

    log.info("############ GenotypeDbxref #############")
    fds = session.query(GenotypeDbxref).filter(GenotypeDbxref.genotype_id == Genotype.genotype_id)
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("############# Phendesc ############")
    scs = session.query(Phendesc).filter(Phendesc.genotype_id == Genotype.genotype_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            log.info(sc)

    log.info("############# Phenstatement ############")
    scs = session.query(Phenstatement).filter(Phenstatement.genotype_id == Genotype.genotype_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            log.info(sc)

    log.info("############# PhenotypeComparison 1 ############")
    scs = session.query(PhenotypeComparison).filter(PhenotypeComparison.genotype1_id == Genotype.genotype_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            log.info(sc)

    log.info("############# PhenotypeComparison 2 ############")
    scs = session.query(PhenotypeComparison).filter(PhenotypeComparison.genotype2_id == Genotype.genotype_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            log.info(sc)


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
    report_Genotype(session, args.Genotype, args.debug, args.limit, args.by)
    # report_Genotype(1, 2, 3, 4) # check mypy type checking is working
