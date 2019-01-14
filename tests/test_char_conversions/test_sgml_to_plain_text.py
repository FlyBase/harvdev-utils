#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `harvdev_utils` package."""
import pytest

from harvdev_utils.char_conversions import sgml_to_plain_text

dict_to_test = {
    '&agr;' : 'alpha',
    '&Agr;' : 'Alpha',
    '&bgr;' : 'beta',
    '&Bgr;' : 'Beta',
    '&ggr;' : 'gamma',
    '&Ggr;' : 'Gamma',
    '&dgr;' : 'delta',
    '&Dgr;' : 'Delta',
    '&egr;' : 'epsilon',
    '&Egr;' : 'Epsilon',
    '&zgr;' : 'zeta',
    '&Zgr;' : 'Zeta',
    '&eegr;' : 'eta',
    '&EEgr;' : 'Eta',
    '&thgr;' : 'theta',
    '&THgr;' : 'Theta',
    '&igr;' : 'iota',
    '&Igr;' : 'Iota',
    '&kgr;' : 'kappa',
    '&Kgr;' : 'Kappa',
    '&lgr;' : 'lambda',
    '&Lgr;' : 'Lambda',
    '&mgr;' : 'mu',
    '&Mgr;' : 'Mu',
    '&ngr;' : 'nu',
    '&Ngr;' : 'Nu',
    '&xgr;' : 'xi',
    '&Xgr;' : 'Xi',
    '&ogr;' : 'omicron',
    '&Ogr;' : 'Omicron',
    '&pgr;' : 'pi',
    '&Pgr;' : 'Pi',
    '&rgr;' : 'rho',
    '&Rgr;' : 'Rho',
    '&sgr;' : 'sigma',
    '&Sgr;' : 'Sigma',
    '&tgr;' : 'tau',
    '&Tgr;' : 'Tau',
    '&ugr;' : 'upsilon',
    '&Ugr;' : 'Upsilon',
    '&phgr;' : 'phi',
    '&PHgr;' : 'Phi',
    '&khgr;' : 'chi',
    '&KHgr;' : 'Chi',
    '&psgr;' : 'psi',
    '&PSgr;' : 'Psi',
    '&ohgr;' : 'omega',
    '&OHgr;' : 'Omega'
    }

@pytest.mark.parametrize('key', dict_to_test.keys())
def test_sgml_to_plain_text(key):
    assert sgml_to_plain_text(dict_to_test[key]) == dict_to_test[key]