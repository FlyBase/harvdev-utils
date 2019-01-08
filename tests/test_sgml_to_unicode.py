#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `harvdev_utils` package."""
import pytest

from harvdev_utils.char_conversions import sgml_to_unicode

dict_to_test = {
    '&agr;' : '\u03B1',
    '&Agr;' : '\u0391',
    '&bgr;' : '\u03B2',
    '&Bgr;' : '\u0392',
    '&ggr;' : '\u03B3',
    '&Ggr;' : '\u0393',
    '&dgr;' : '\u03B4',
    '&Dgr;' : '\u0394',
    '&egr;' : '\u03B5',
    '&Egr;' : '\u0395',
    '&zgr;' : '\u03B6',
    '&Zgr;' : '\u0396',
    '&eegr;' : '\u03B7',
    '&EEgr;' : '\u0397',
    '&thgr;' : '\u03B8',
    '&THgr;' : '\u0398',
    '&igr;' : '\u03B9',
    '&Igr;' : '\u0399',
    '&kgr;' : '\u03BA',
    '&Kgr;' : '\u039A',
    '&lgr;' : '\u03BB',
    '&Lgr;' : '\u039B',
    '&mgr;' : '\u03BC',
    '&Mgr;' : '\u039C',
    '&ngr;' : '\u03BD',
    '&Ngr;' : '\u039D',
    '&xgr;' : '\u03BE',
    '&Xgr;' : '\u039E',
    '&ogr;' : '\u03BF',
    '&Ogr;' : '\u039F',
    '&pgr;' : '\u03C0',
    '&Pgr;' : '\u03A0',
    '&rgr;' : '\u03C1',
    '&Rgr;' : '\u03A1',
    '&sgr;' : '\u03C3',
    '&Sgr;' : '\u03A3',
    '&tgr;' : '\u03C4',
    '&Tgr;' : '\u03A4',
    '&ugr;' : '\u03C5',
    '&Ugr;' : '\u03A5',
    '&phgr;' : '\u03C6',
    '&PHgr;' : '\u03A6',
    '&khgr;' : '\u03C7',
    '&KHgr;' : '\u03A7',
    '&psgr;' : '\u03C8',
    '&PSgr;' : '\u03A8',
    '&ohgr;' : '\u03C9',
    '&OHgr;' : '\u03A9'
    }

@pytest.mark.parametrize('key', dict_to_test.keys())
def test_sgml_to_unicode(key):
    assert sgml_to_unicode(dict_to_test[key]) == dict_to_test[key]