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

from harvdev_utils.chado_functions import (
    get_cvterm, check_cvterm_has_prop, check_cvterm_is_allowed, CodingError
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

    def test_cvterm_lookup(self):
        cvterm = get_cvterm(session, 'FlyBase miscellaneous CV', 'pheno1')
        assert cvterm.cvterm_id != 0

        found = check_cvterm_has_prop(session, cvterm, 'bad_prop')
        assert found == False

        found = check_cvterm_has_prop(session, cvterm, 'phenotypic_class')
        assert found == True

    def test_cvterm_allowed(self):
        cvterm = get_cvterm(session, 'FlyBase miscellaneous CV', 'pheno1')
        assert cvterm.cvterm_id != 0
        allowed = check_cvterm_is_allowed(session, cvterm, ['FBcv:environmental_qualifier', 'FBcv:phenotypic_class'])
        assert allowed == True

    def test_cvterm_not_allowed(self):
        cvterm = get_cvterm(session, 'property type', 'GO_internal_notes')
        assert cvterm.cvterm_id != 0
        allowed = check_cvterm_is_allowed(session, cvterm, ['FBcv:environmental_qualifier', 'FBcv:phenotypic_class'])
        assert allowed == False

    def test_bad_list(self):
        cvterm = get_cvterm(session, 'FlyBase miscellaneous CV', 'pheno1')
        with pytest.raises(CodingError):
            allowed = check_cvterm_is_allowed(session, cvterm, ['badformat'])

    def test_empty_list(self):
        cvterm = get_cvterm(session, 'FlyBase miscellaneous CV', 'pheno1')
        with pytest.raises(CodingError):
            allowed = check_cvterm_is_allowed(session, cvterm, ['FBcv:madeupcvterm'])
