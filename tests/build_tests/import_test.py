#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `harvdev_utils` package."""
import unittest

from harvdev_utils.char_conversions import (
    sgml_to_plain_text, sgml_to_unicode,
    unicode_to_plain_text, sub_sup_to_sgml
)
from harvdev_utils.chado_functions import get_or_create, ExternalLookup, get_cvterm, CodingError
#from harvdev_utils.harvdev_utils.chado_functions.chado_errors import CodingError 

def test_import():
    # will not get here unless all the module are installed.
    assert 1