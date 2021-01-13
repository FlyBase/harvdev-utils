#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `harvdev_utils` package."""
import unittest
import pytest
import os
import time
import psycopg2
import subprocess

# Minimal prototype test for new proforma parsing software.
# SQL Alchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from harvdev_utils.chado_functions import (
    get_feature_by_uniquename, feature_name_lookup,
    feature_symbol_lookup, feature_synonym_lookup,
    get_organism, CodingError, DataError
)
conn2 = False
session = None

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    global conn2, session
    conn2 = module.conn = startup_db()
    session = get_session()

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    stop_db(module.conn)

def stop_db(conn):
    """Shut down the test database instance."""
    output = subprocess.getoutput('docker rm $(docker stop $(docker ps -a -q --filter ancestor=flybase/proformatestdb --format="{{.ID}}"))')
    if conn:
        conn.close()


def startup_db():
    """Start up the test database instance."""
    # This first os.system command is a bit hacky, but it'll prevent errors where the database is already running
    # and we attempt to execute 'docker run' again. TODO Revisit this and handle "docker is already running" issues better.
    os.system('docker rm $(docker stop $(docker ps -a -q --filter ancestor=flybase/proformatestdb --format="{{.ID}}"))')
    os.system('docker run -p 127.0.0.1:5436:5432 --name harv_util_proformatestdb flybase/proformatestdb &')

    conn = None
    trys = 0
    while (not conn and trys < 10):
        trys += 1
        time.sleep(5)
        try:
            conn = psycopg2.connect(host="127.0.0.1", port="5436", database="fb_test", user='tester', password="tester")
        except psycopg2.Error:
            pass

    if (not conn):
        print("ERROR: Could not connect to test db")
        stop_db(None)
        exit(-1)

    return conn

def get_session():
    # Create our SQL Alchemy engine from our environmental variables.
    engine_var = 'postgresql://' + 'tester' + ":" + 'tester' + '@' + '127.0.0.1' + ':' + '5436' '/' + 'fb_test'

    engine = create_engine(engine_var)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session

class TestSomething:

    def test_unique_lookup_good(self):
        """Test uniquename good lookups."""

        # standard lookup
        feature = get_feature_by_uniquename(session, "FBgn0004700")
        assert feature.name == 'symbol-47'

        # lookup with obsolete set.
        feature = get_feature_by_uniquename(session, "FBgn0004800", obsolete='f')
        assert feature.name == 'symbol-48'

        # check obsolete = 'e' => either. 
        feature = get_feature_by_uniquename(session, "FBgn0004900", obsolete='e')
        assert feature.name == 'symbol-49'

    def test_unique_lookup_bad(self):
        """Test uniquename bad lookups."""

       # lookup up non allowed obsolete value
        with pytest.raises(CodingError):
            feature = get_feature_by_uniquename(session, "FBgn0004600", obsolete='madeup')

        # obsolete wrong.
        with pytest.raises(NoResultFound):
            feature = get_feature_by_uniquename(session, "FBgn0004500", obsolete='t')

        # lookup up non existant uniquename
        with pytest.raises(NoResultFound):
            feature = get_feature_by_uniquename(session, "Made_Ip", obsolete='t')
        

    def test_name_lookup_good(self):
        """Test name good lookups."""

        # check basic lookup
        feature = feature_name_lookup(session, 'symbol-1')
        assert feature.uniquename == 'FBgn0000100'

        # check type_name and obsolete work
        feature = feature_name_lookup(session, 'symbol-2', type_name='gene', obsolete='f')
        assert feature.uniquename == 'FBgn0000200'

        # check obsolete 'e' 
        feature = feature_name_lookup(session, 'symbol-3', obsolete='e')
        assert feature.uniquename == 'FBgn0000300'

        # check organism start in name
        organism = get_organism(session, short='Hsap')
        feature = feature_name_lookup(session, 'Hsap\\symbol-1', organism_id=organism.organism_id)
        assert feature.uniquename == 'FBgn0000101'

        # check converted greek chars are done correctly.
        feature = feature_name_lookup(session, 'genechar-alpha-[0002]')
        feature.name == 'genechar-alpha-[0002]'

    def test_name_lookup_bad(self):
        """Test name bad lookups."""

        # check for bad made up name
        feature = feature_name_lookup(session, 'madeup_name')
        assert feature == None

        # Check that obsolete is used and checked
        feature = feature_name_lookup(session, 'symbol-4', type_name='gene', obsolete='t')
        assert feature == None

        # check type_name is checked
        feature = feature_name_lookup(session, 'symbol-5', type_name='allele', obsolete='f')
        assert feature == None

    def test_symbol_lookup_good(self):
        """Test symbol good lookups.
        
        Note symbols are unique, synonyms are NOT, that is the difference.
        """

        # Check standard use.
        feature = feature_symbol_lookup(session, 'gene', 'symbol-10')
        assert feature.name == 'symbol-10'

        # Add obsolete as 'f'
        feature = feature_symbol_lookup(session, 'gene', 'symbol-11', obsolete='f')
        assert feature.name == 'symbol-11'

        # Add obsolete as 'e'
        feature = feature_symbol_lookup(session, 'gene', 'symbol-12', obsolete='e')
        assert feature.name == 'symbol-12'
 
        # lookup diff species.
        organism = get_organism(session, short='Hsap')
        feature = feature_symbol_lookup(session, 'gene', 'Hsap\\symbol-20', organism_id=organism.organism_id)
        assert feature.name == 'Hsap\\symbol-20'
        assert feature.organism_id == organism.organism_id

        # check greek chars are done correctly.
        feature = feature_symbol_lookup(session, 'gene', 'genechar-&agr;-[0002]')
        assert feature.name == 'genechar-alpha-[0002]'

       # DO NOT specify a type, look for all 
        feature = feature_symbol_lookup(session, None, 'symbol-21')
        assert feature.uniquename == 'FBgn0002100'

        # Test bracket names with no conversion (convert = false)
        feature = feature_symbol_lookup(session, None, 'C9orf72:n.intron14[30GGGGCC]', convert=False)
        assert feature.name == 'C9orf72:n.intron14[30GGGGCC]'
    
    def test_symbol_lookup_bad(self):
        """Test symbol bad lookups."""

        # Lookup non existent symbol
        with pytest.raises(NoResultFound):
            feature = feature_symbol_lookup(session, 'gene', 'made up')

        # Lookup with incorrect obsolete value
        with pytest.raises(NoResultFound):
            feature = feature_symbol_lookup(session, 'gene', 'symbol-30', obsolete='t')

        # default org is Dmel so choose Hsap synonym as test
        organism = get_organism(session, short='Hsap')
        with pytest.raises(NoResultFound):
            feature = feature_symbol_lookup(session, 'gene', 'symbol-30', organism_id=organism.organism_id)

        # wrong type.
        with pytest.raises(NoResultFound):
            feature = feature_symbol_lookup(session, 'allele', 'genechar-&agr;-[0002]')

        # DIVS do not convert but do not specift here so it should fail
        with pytest.raises(NoResultFound):
            feature = feature_symbol_lookup(session, None, 'C9orf72:n.intron14[30GGGGCC]')

    def test_synonym_lookup_good(self):
        """Test synonym good lookups."""

        # return array if cheque_unique not used
        features = feature_synonym_lookup(session, 'gene', 'symbol-1')
        for feature in features:
            assert feature.uniquename in ['FBgn0000100']

        # lookup diff species.
        organism = get_organism(session, short='Hsap')
        feature = feature_synonym_lookup(session, 'gene', 'Hsap\\symbol-20', organism_id=organism.organism_id)
        assert feature.uniquename in ['FBgn0002001']

         # return feature if check_unique if set
        feature = feature_synonym_lookup(session, 'gene', 'symbol-2', check_unique=True)
        assert feature.uniquename in ['FBgn0000200']

        # return feature if check_unique if set and obsolete is 'f'
        feature = feature_synonym_lookup(session, 'gene', 'symbol-3', check_unique=True, obsolete='f')
        assert feature.uniquename in ['FBgn0000300']

        # return feature if check_unique if set and obsolete is 'e' => either
        feature = feature_synonym_lookup(session, 'gene', 'symbol-4', check_unique=True, obsolete='e')
        assert feature.uniquename in ['FBgn0000400']



    def test_synonym_lookup_bad(self):
        """Test synonym bad lookups."""

        # gene does not exist
        features = feature_synonym_lookup(session, 'gene', 'made_up')
        assert not features

        # gene does not exist make it unique
        with pytest.raises(DataError):
            feature = feature_synonym_lookup(session, 'gene', 'made_up', check_unique=True)

        # return feature if check_unique if set and obsolete is 'e' => either
        with pytest.raises(DataError):
            feature = feature_synonym_lookup(session, 'gene', 'symbol-6', check_unique=True, obsolete='t')

        # return feature  obsolete is 't' NO checkunique
        features = feature_synonym_lookup(session, 'gene', 'symbol-6', obsolete='t')
        assert not features


