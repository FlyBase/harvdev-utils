"""CellLine Report.

Code to display all CellLine data and relationships etc for a given CellLine.

Can be used as the basis for future proforma work.

i.e. python CellLine_report.py -c chado.cfg -f SIP_S1_8 -l 2



* => added

 public | cell_line_cvterm                                                | table    | go
 public | cell_line_cvtermprop                                            | table    | go
 public | cell_line_dbxref                                                | table    | go
 public | cell_line_feature                                               | table    | go
 public | cell_line_library                                               | table    | go
 public | cell_line_libraryprop                                           | table    | go
 public | cell_line_pub                                                   | table    | go
 public | cell_line_relationship                                          | table    | go
 public | cell_line_Strain                                                | table    | go
 public | cell_line_Strainprop                                            | table    | go
 public | cell_line_synonym                                               | table    | go
 public | cell_lineprop                                                   | table    | go
 public | cell_lineprop_pub                                               | table    | go

"""
import argparse
import configparser
import logging
import sys
from typing import Union

# Minimal prototype test for new proforma parsing software.
# SQL Alchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from harvdev_utils.production import (CellLine, CellLineCvterm, CellLineCvtermprop,
                                      CellLineDbxref, CellLineFeature,
                                      CellLineprop,
                                      CellLinepropPub, CellLinePub,
                                      CellLineLibrary, CellLineLibraryprop,
                                      CellLineStrain, CellLineStrainprop,
                                      CellLineRelationship, CellLineSynonym)
from sqlalchemy.orm.session import Session

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--CellLine', help=' (CellLine symbol to make report for)', required=True)
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


def get_CellLine(session: Session, symbol: str, lookup_by: str) -> Union[CellLine, None]:
    """Lookup CellLine."""
    cell_line = None
    log.info("Looking up CellLine '{}' using method '{}'".format(symbol, lookup_by))
    try:
        if lookup_by == 'name':
            cell_line = session.query(CellLine).filter(CellLine.name == symbol).one()
        elif lookup_by == 'uniquename':
            cell_line = session.query(CellLine).filter(CellLine.uniquename == symbol).one()
    except NoResultFound:
        log.info("Could NOT find '{}' by {}. exiting".format(symbol, lookup_by))
        exit(-1)
    except MultipleResultsFound:
        log.info("Could NOT find UNIQUE entry for '{}' by {}. exiting".format(symbol, lookup_by))
        exit(-1)
    return cell_line


def report_CellLine(session: Session, symbol: str, debug: bool, limit: int, lookup_by: str):  # noqa
    """Write report."""
    ###########################
    # starting point for report
    ###########################
    CellLine = get_CellLine(session, symbol, lookup_by)
    if not CellLine:
        return
    log.info("###################### CellLine ############################")
    log.info(CellLine)
    log.info("###########################################################")
    # log.info(dir(feature))

    log.info("\n################### CellLinePub #####################")
    fps = session.query(CellLinePub).filter(CellLinePub.cell_line_id == CellLine.cell_line_id)
    count = 0
    for fp in fps:
        count += 1
        if not limit or count <= limit:
            log.info(fp)

    log.info("\n################### CellLineprop #####################")
    sps = session.query(CellLineprop).filter(CellLineprop.cell_line_id == CellLine.cell_line_id)
    count = 0
    for sp in sps:
        count += 1
        spps = session.query(CellLinepropPub).filter(CellLinepropPub.cell_lineprop_id == sp.cell_lineprop_id)
        for spp in spps:
            if not limit or count <= limit:
                log.info("CellLinepropPub id={}: CellLineprop id={} pub:{}".format(spp.cell_lineprop_pub_id, sp.cell_lineprop_id, spp.pub))
        log.info(sp)

    log.info("\n################### Synonyms ##############################")
    fss = session.query(CellLineSynonym).filter(CellLineSynonym.cell_line_id == CellLine.cell_line_id)
    count = 0
    for fs in fss:
        count += 1
        if not limit or count <= limit:
            log.info(fs)

    log.info("\n############# Features ##################")
    sfs = session.query(CellLineFeature).filter(CellLineFeature.cell_line_id == CellLine.cell_line_id)
    count = 0
    for sf in sfs:
        count += 1
        if not limit or count <= limit:
            log.info(sf)

    log.info("\n############# Subject Relationships ##################")
    srs = session.query(CellLineRelationship).filter(CellLineRelationship.subject_id == CellLine.cell_line_id)
    count = 0
    for sr in srs:
        count += 1
        if not limit or count <= limit:
            log.info(sr)

    log.info("############# Object Relationships ##################")
    srs = session.query(CellLineRelationship).filter(CellLineRelationship.object_id == CellLine.cell_line_id)
    count = 0
    for sr in srs:
        count += 1
        if not limit or count <= limit:
            log.info(sr)

    log.info("############# CellLineCvtermxxxx ############")
    scs = session.query(CellLineCvterm).filter(CellLineCvterm.cell_line_id == CellLine.cell_line_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            scps = session.query(CellLineCvtermprop).filter(CellLineCvtermprop.cell_line_cvterm_id == sc.cell_line_cvterm_id)
            for scp in scps:
                mess = "CellLineCvtermprop id={} CellLineCvterm id={}: rank={} value='{}' type=({})".\
                    format(scp.cell_line_cvtermprop_id, sc.cell_line_cvterm_id, scp.rank, scp.value, scp.type)
                log.info(mess)
            log.info(sc)

    log.info("############ CellLineDbxref #############")
    fds = session.query(CellLineDbxref).filter(CellLineDbxref.cell_line_id == CellLine.cell_line_id)
    count = 0
    for fd in fds:
        count += 1
        if not limit or count <= limit:
            log.info(fd)

    log.info("############# CellLineLibrayxxxx ############")
    scs = session.query(CellLineLibrary).filter(CellLineLibrary.cell_line_id == CellLine.cell_line_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            scps = session.query(CellLineLibraryprop).filter(CellLineLibraryprop.cell_line_library_id == sc.cell_line_library_id)
            for scp in scps:
                mess = "CellLineLibraryprop id={} CellLineLibrary id={}: rank={} value='{}' type=({})".\
                    format(scp.cell_line_libraryprop_id, sc.cell_line_library_id, scp.rank, scp.value, scp.type)
                log.info(mess)
            log.info(sc)

    log.info("############# CellLineStrainxxxx ############")
    scs = session.query(CellLineStrain).filter(CellLineStrain.strain_id == CellLine.cell_line_id)
    count = 0
    for sc in scs:
        count += 1
        if not limit or count <= limit:
            scps = session.query(CellLineStrainprop).filter(CellLineStrainprop.cell_line_strain_id == sc.cell_line_strain_id)
            for scp in scps:
                mess = "CellLineLibraryprop id={} CellLineLibrary id={}: rank={} value='{}' type=({})".\
                    format(scp.cell_line_cvtermprop_id, sc.cell_line_cvterm_id, scp.rank, scp.value, scp.type)
                log.info(mess)
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
    report_CellLine(session, args.CellLine, args.debug, args.limit, args.by)
    # report_CellLine(1, 2, 3, 4) # check mypy type checking is working
