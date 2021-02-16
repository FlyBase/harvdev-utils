#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `harvdev_utils` package checks.py file."""
import unittest

from harvdev_utils.general_functions import (
    xort_logfile_check, proforma_logfile_check, check_xml, new_proforma_logfile_check
)

def test_xml_good():
    # will not get here unless all the module are installed.
    okay, error_string = check_xml("./tests/test_general_functions/test_data_files/good_test.xml")
    assert okay
    assert error_string == ""

def test_xml_bad():
    # will not get here unless all the module are installed.
    okay, error_string = check_xml("./tests/test_general_functions/test_data_files/bad_test.xml")
    assert not okay
    assert "does not end in '</chado>'" in error_string

def test_xml_empty():
    # Test we get an error and message lives up to that.
    okay, error_string = check_xml("./tests/test_general_functions/test_data_files/empty_test.xml")
    assert not okay
    assert "Empty" in error_string

def test_old_proforma_good():
    # will not get here unless all the module are installed.
    okay, error_string = proforma_logfile_check("./tests/test_general_functions/test_data_files/old_proforma_good.log")
    assert okay
    assert error_string == ""

def test_old_proforma_bad():
    # will not get here unless all the module are installed.
    okay, error_string = proforma_logfile_check("./tests/test_general_functions/test_data_files/old_proforma_bad.log")
    assert not okay
    assert "file:al2794.edit" in error_string

def test_old_proforma_empty():
    # Test we get an error and message lives up to that.
    okay, error_string = proforma_logfile_check("./tests/test_general_functions/test_data_files/old_proforma_empty.log")
    assert not okay
    assert "Empty" in error_string

def test_xort_log_good():
    # will not get here unless all the module are installed.
    okay, error_string = xort_logfile_check("./tests/test_general_functions/test_data_files/xort_good.log")
    assert okay
    assert error_string == ""

def test_xort_log_bad():
    # will not get here unless all the module are installed.
    okay, error_string = xort_logfile_check("./tests/test_general_functions/test_data_files/xort_bad.log")
    assert not okay
    assert "Error: NO 'bingo ....you success' found" in error_string

def test_xort_log_empty():
    # Test we get an error and message lives up to that.
    okay, error_string = xort_logfile_check("./tests/test_general_functions/test_data_files/xort_empty.log")
    assert not okay
    assert "Empty" in error_string

def test_new_proforma_good():
    # will not get here unless all the module are installed.
    okay, error_string = new_proforma_logfile_check("./tests/test_general_functions/test_data_files/new_proforma_good.log")
    assert okay
    assert error_string == ""

def test_new_proforma_bad():
    # will not get here unless all the module are installed.
    okay, error_string = new_proforma_logfile_check("./tests/test_general_functions/test_data_files/new_proforma_bad.log")
    assert not okay
    assert "Error: NO 'bingo ....you success' found" in error_string

def test_new_proforma_empty():
    # Test we get an error and message lives up to that.
    okay, error_string = new_proforma_logfile_check("./tests/test_general_functions/test_data_files/new_proforma_empty.log")
    assert not okay
    assert "Empty" in error_string

