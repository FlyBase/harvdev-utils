"""Report summary for a feature."""
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy import create_engine
import configparser
import os
import logging

from harvdev_utils.chado_functions import (feature_name_lookup,
                                           feature_symbol_lookup,
                                           get_feature_by_uniquename)
from harvdev_utils.production import (FeatureCvterm, FeatureCvtermDbxref,
                                      FeatureCvtermprop,
                                      FeatureExpression, FeatureGenotype,
                                      FeatureGrpmember,
                                      FeatureHumanhealthDbxref,
                                      FeatureInteraction, Featureloc, FeaturePhenotype,
                                      Featureprop, FeaturepropPub, FeaturePub,
                                      FeatureRelationship, FeatureRelationshipPub,
                                      FeatureRelationshipprop,
                                      HumanhealthFeature,
                                      LibraryFeature, LibraryFeatureprop,
                                      Phenstatement)

log = logging.getLogger(__name__)


def get_config_from_file(cfg_file):
    """Import secure config variables."""
    config = configparser.ConfigParser()
    config.read(cfg_file)
    if 'connection' not in config:
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
    return config


def create_postgres_session(config_file=None, config=None, noheader=False):
    """Connect to database."""
    if config_file:
        config = get_config_from_file(config_file)

    USER = config['connection']['USER']
    PASSWORD = config['connection']['PASSWORD']
    SERVER = config['connection']['SERVER']
    try:
        PORT = config['connection']['PORT']
    except KeyError:
        PORT = '5432'

    DB = config['connection']['DB']

    if not noheader:
        print('Using server: {}'.format(SERVER))
        print('Using database: {}'.format(DB))

    # Create our SQL Alchemy engine from our environmental variables.
    engine_var = 'postgresql://' + USER + ":" + PASSWORD + '@' + SERVER + ':' + PORT + '/' + DB
    engine = create_engine(engine_var)

    Session = sessionmaker(bind=engine)
    session = Session()

    return session


def get_feature(session, feature_symbol, feature_type, lookup_by, obsolete, noheader):
    """Lookup feature."""
    if not noheader:
        print("Looking up feature '{}' of type '{}' using method '{}' an obsolete='{}'".format(feature_symbol, feature_type, lookup_by, obsolete))
    try:
        if lookup_by == 'symbol':
            return feature_symbol_lookup(session, feature_type, feature_symbol, obsolete=obsolete)
        elif lookup_by == 'name':
            return feature_name_lookup(session, feature_symbol, type_name=feature_type, obsolete=obsolete)
        elif lookup_by == 'uniquename':
            return get_feature_by_uniquename(session, feature_symbol, feature_type, obsolete=obsolete)
    except NoResultFound:
        print("Could NOT find '{}' of type '{}'. exiting".format(feature_symbol, feature_type))
        exit(-1)
    except MultipleResultsFound:
        print("Could NOT find UNIQUE entry for '{}' of type '{}'. exiting".format(feature_symbol, feature_type))
        if lookup_by == 'symbol':
            features = feature_symbol_lookup(session, feature_type, feature_symbol, check_unique=False, obsolete=obsolete)
            for feature in features:
                print("{}".format(feature))
        exit(-1)


def report(session, feature_symbol, feature_type, debug, limit, lookup_by, obsolete, noheader):
    """Write report."""
    ###########################
    # starting point for report
    ###########################
    feature = get_feature(session, feature_symbol, feature_type, lookup_by, obsolete, noheader)

    if not feature:
        raise ValueError("Feature NOT found")
    print("'{}' feature: '{}' '{}' org:'{}'".format(feature.type.name, feature.name, feature.uniquename, feature.organism.abbreviation))

    fis = session.query(Featureloc).filter(Featureloc.feature_id == feature.feature_id)
    for fd in fis:
        print("\tLocation: {}:{} {}".format(fd.srcfeature.type.name, fd.srcfeature.name, fd.strand))

    pub_list = []
    fps = session.query(FeaturePub).filter(FeaturePub.feature_id == feature.feature_id)
    count = 0
    for fp in fps:
        count += 1
        if not limit or count <= limit:
            pub_list.append(fp.pub.uniquename)
    if pub_list:
        print("Pubs linked: {}".format(pub_list))

    fps = session.query(Featureprop).filter(Featureprop.feature_id == feature.feature_id)
    count = 0
    for fp in fps:
        if not count:
            print("Props")
        pub_list = []
        count += 1
        fpps = session.query(FeaturepropPub).filter(FeaturepropPub.featureprop_id == fp.featureprop_id)
        for fpp in fpps:
            if not limit or count <= limit:
                pub_list.append(fpp.pub.uniquename)
        if not limit or count <= limit:
            message = "\tprop:'{}' value:'{}' pubs:'{}'".\
                format(fp.type.name, fp.value, pub_list)
            print(message)

    # print("################### Synonyms ##############################")
    # fss = session.query(FeatureSynonym).filter(FeatureSynonym.feature_id == feature.feature_id)
    # count = 0
    # for fs in fss:
    #     count += 1
    #     if not limit or count <= limit:
    #         print(fs)

    frs = session.query(FeatureRelationship).filter(FeatureRelationship.subject_id == feature.feature_id)
    count = 0
    for fr in frs:
        if not count:
            print("Relationships")
        count += 1
        prop_list = []
        pub_list = []
        frps = session.query(FeatureRelationshipprop).\
            filter(FeatureRelationshipprop.feature_relationship_id == fr.feature_relationship_id)
        for frp in frps:
            prop_list.append("{} {}".format(frp.feature_relationship.type.name, frp.value))
        frpubs = session.query(FeatureRelationshipPub).\
            filter(FeatureRelationshipPub.feature_relationship_id == fr.feature_relationship_id)
        for frpub in frpubs:
            pub_list.append(frpub.pub.uniquename)
        print("\tObject '{}' '{}': cvterm:'{}' props: '{}' pubs '{}'".format(fr.object.uniquename, fr.object.name, fr.type.name, prop_list, pub_list))

    frs = session.query(FeatureRelationship).filter(FeatureRelationship.object_id == feature.feature_id)
    for fr in frs:
        if not count:
            print("Relationships")
        count += 1
        prop_list = []
        pub_list = []
        frps = session.query(FeatureRelationshipprop).\
            filter(FeatureRelationshipprop.feature_relationship_id == fr.feature_relationship_id)
        for frp in frps:
            prop_list.append("{} {}".format(frp.feature_relationship.type.name, frp.value))
        frpubs = session.query(FeatureRelationshipPub).\
            filter(FeatureRelationshipPub.feature_relationship_id == fr.feature_relationship_id)
        for frpub in frpubs:
            pub_list.append(frpub.pub.uniquename)
        print("\tSubject '{}' '{}': type:'{}' props: '{}' pubs '{}'".format(fr.subject.uniquename, fr.subject.name, fr.type.name, prop_list, pub_list))

    if (0):  # TODO
        print("############# HumanhealthFeature #######")
        fhds = session.query(HumanhealthFeature).filter(HumanhealthFeature.feature_id == feature.feature_id)
        count = 0
        for fhd in fhds:
            count += 1
            if not limit or count <= limit:
                print(fhd)

        print("############# FeatureHumanhealthDbxref #######")
        fhds = session.query(FeatureHumanhealthDbxref).filter(FeatureHumanhealthDbxref.feature_id == feature.feature_id)
        count = 0
        for fhd in fhds:
            count += 1
            if not limit or count <= limit:
                print(fhd)

    fcs = session.query(FeatureCvterm).filter(FeatureCvterm.feature_id == feature.feature_id)
    count = 0
    for fc in fcs:
        dbx_list = []
        prop_list = []
        fcds = session.query(FeatureCvtermDbxref).filter(FeatureCvtermDbxref.feature_cvterm_id == fc.feature_cvterm_id)
        for fcd in fcds:
            dbx_list.append(fcd.dbxref)
        fcds = session.query(FeatureCvtermprop).filter(FeatureCvtermprop.feature_cvterm_id == fc.feature_cvterm_id)
        for fcd in fcds:
            prop_list.append(fcd.type.name)
        if not count:
            print("cvterms")
            count += 1
        print("\tcvterm:'{}' dbxs:'{}' props"'{}'.format(fc.cvterm.name, dbx_list, prop_list))

    # fds = session.query(FeatureDbxref).filter(FeatureDbxref.feature_id == feature.feature_id)
    # count = 0
    # for fd in fds:
    #    if not count:
    #        print("############ FeatureDbxref #############")
    #    count += 1
    #    print(fd)

    fds = session.query(FeatureExpression).filter(FeatureExpression.feature_id == feature.feature_id)
    count = 0
    for fd in fds:
        if not count:
            print("############ FeatureExpression #############")
        print(fd)
        count += 1

    fgs = session.query(FeatureGenotype).filter(FeatureGenotype.feature_id == feature.feature_id)
    count = 0
    for fg in fgs:
        # print(dir(fg))
        # print(fg)
        if not count:
            print("Phenstatements:-")
        count += 1
        line = "genotype:'{}' ".format(fg.genotype.uniquename)

        pss = session.query(Phenstatement).filter(Phenstatement.genotype_id == fg.genotype_id)
        if pss:
            for phen_statement in pss:
                phenotype = phen_statement.phenotype
                line += "\tphenotype:'{}' cvterm:{} val:{}".\
                    format(phenotype.uniquename,
                           phenotype.cvalue.name,
                           phenotype.value)
                if phen_statement.type.name != 'unspecified':
                    line += ' env:{}'.format(phen_statement.type.name)
                if phen_statement.environment.uniquename != 'unspecified':
                    line += ' env:{}'.format(phen_statement.environment.uniquename)

                if phenotype.assay.name != 'unspecified':
                    line += ' assay:{}'.format(phenotype.assay.name)
                if phenotype.attr.name != 'unspecified':
                    line += ' attr:{}'.format(phenotype.attr.name)
                print("\t", line)
        else:
            print("\t", line)

    fds = session.query(FeaturePhenotype).filter(FeaturePhenotype.feature_id == feature.feature_id)
    count = 0
    for fd in fds:
        if not count:
            print("############ FeaturePhenotype #############")
        count += 1
        print(fd)

    fds = session.query(FeatureGrpmember).filter(FeatureGrpmember.feature_id == feature.feature_id)
    count = 0
    for fd in fds:
        if not count:
            print("############ FeatureGrpMember #############")
        count += 1
        print(fd)

    fis = session.query(FeatureInteraction).filter(FeatureInteraction.feature_id == feature.feature_id)
    count = 0
    for fd in fis:
        if not count:
            print("############ FeatureInteraction #############")
        count += 1
        if not limit or count <= limit:
            print(fd)

    lfs = session.query(LibraryFeature).filter(LibraryFeature.feature_id == feature.feature_id)
    count = 0
    for lf in lfs:
        if not count:
            print("########### LibraryFeature ###########")
        count += 1
        seen = False
        lfps = session.query(LibraryFeatureprop).filter(LibraryFeatureprop.library_feature_id == lf.library_feature_id)
        for lfp in lfps:
            seen = True
            print(lfp)
        if not seen:
            print(lf)
